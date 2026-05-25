from typing import Dict, Any, TypedDict
import logging, re

try:
    from langgraph.graph import StateGraph, END
    from langchain_groq import ChatGroq
    LLM_OK = True
except ImportError:
    LLM_OK = False

from config import settings

logger = logging.getLogger(__name__)


class State(TypedDict):
    user_query: str
    research_data: str
    summary: str
    critique: str
    refined_output: str
    iteration: int
    max_iterations: int
    critique_score: int


class Workflow:
    def __init__(self):
        self.max_iterations = settings.MAX_ITERATIONS
        self.critique_threshold = settings.CRITIQUE_THRESHOLD
        self._graph = None

    def _llm(self, temp=0.7):
        if not LLM_OK:
            return None
        if settings.GROQ_API_KEY:
            return ChatGroq(model=settings.LLM_MODEL, temperature=temp, groq_api_key=settings.GROQ_API_KEY)
        return None

    def build(self):
        g = StateGraph(State)
        g.add_node("researcher", self.research)
        g.add_node("summarizer", self.summarize)
        g.add_node("critic", self.critique)
        g.add_node("refiner", self.refine)
        g.add_edge("researcher", "summarizer")
        g.add_edge("summarizer", "critic")
        g.add_conditional_edges("critic", self.decide, {"refiner": "refiner", END: END})
        g.add_edge("refiner", "critic")
        g.set_entry_point("researcher")
        return g.compile()

    @property
    def graph(self):
        if not self._graph:
            self._graph = self.build()
        return self._graph

    def research(self, state: State) -> State:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(state["user_query"], max_results=5))
                state["research_data"] = "\n\n".join(r.get("body", "") for r in results)
        except Exception as e:
            state["research_data"] = f"Search error: {e}"
        return state

    def summarize(self, state: State) -> State:
        llm = self._llm(settings.LLM_TEMPERATURE)
        if llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                r = llm.invoke([
                    SystemMessage(content="Summarize the research concisely."),
                    HumanMessage(content=f"Research: {state['research_data']}\nQuery: {state['user_query']}")
                ])
                state["summary"] = r.content
                return state
            except:
                pass
        state["summary"] = state["research_data"][:1000]
        return state

    def critique(self, state: State) -> State:
        llm = self._llm(0.3)
        if llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                r = llm.invoke([
                    SystemMessage(content="Rate 1-10. Return format: Score: X/10"),
                    HumanMessage(content=f"Query: {state['user_query']}\nSummary: {state['summary']}")
                ])
                state["critique"] = r.content
                m = re.search(r"(\d+)/10", r.content)
                state["critique_score"] = int(m.group(1)) if m else 5
                return state
            except:
                pass
        state["critique"] = "Auto-pass (LLM unavailable)"
        state["critique_score"] = self.critique_threshold
        return state

    def refine(self, state: State) -> State:
        state["iteration"] += 1
        llm = self._llm(0.5)
        if llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                r = llm.invoke([
                    SystemMessage(content="Improve this summary based on critique."),
                    HumanMessage(content=f"Summary: {state['summary']}\nCritique: {state['critique']}\nQuery: {state['user_query']}")
                ])
                state["refined_output"] = r.content
                return state
            except:
                pass
        state["refined_output"] = state["summary"]
        return state

    def decide(self, state: State):
        if state["iteration"] >= state["max_iterations"]:
            return END
        if state["critique_score"] >= self.critique_threshold:
            return END
        return "refiner"

    def run(self, query: str) -> Dict[str, Any]:
        s: State = {
            "user_query": query, "research_data": "", "summary": "",
            "critique": "", "refined_output": "", "iteration": 0,
            "max_iterations": self.max_iterations, "critique_score": 0,
        }
        return self.graph.invoke(s)
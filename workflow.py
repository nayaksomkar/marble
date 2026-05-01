from typing import Dict, Any, TypedDict
import logging

try:
    from langgraph.graph import StateGraph, END
    from langchain_groq import ChatGroq
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LangGraph dependencies not available")

from config import settings

logger = logging.getLogger(__name__)


class ResearchState(TypedDict):
    user_query: str
    research_data: str
    summary: str
    critique: str
    refined_output: str
    iteration: int
    max_iterations: int
    critique_score: int


class WorkflowOrchestrator:
    def __init__(self):
        self.max_iterations = settings.MAX_ITERATIONS
        self.critique_threshold = settings.CRITIQUE_THRESHOLD
        self._graph = None

    def _get_llm(self, temperature: float = 0.7):
        if not LLM_AVAILABLE:
            return None

        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
            try:
                return ChatGroq(
                    model=settings.LLM_MODEL,
                    temperature=temperature,
                    groq_api_key=settings.GROQ_API_KEY
                )
            except Exception as e:
                logger.warning(f"Groq failed: {e}, trying fallback...")

        if settings.MISTRAL_API_KEY and settings.MISTRAL_API_KEY != "your_mistral_api_key_here":
            try:
                from langchain_mistralai import ChatMistralAI
                return ChatMistralAI(
                    model="mistral-large-latest",
                    temperature=temperature,
                    mistral_api_key=settings.MISTRAL_API_KEY
                )
            except Exception as e:
                logger.warning(f"Mistral fallback failed: {e}")

        logger.warning("No valid API keys found. Using fallback summarizer.")
        return None

    def build_graph(self) -> StateGraph:
        workflow = StateGraph(ResearchState)
        workflow.add_node("researcher", self.research_agent)
        workflow.add_node("summarizer", self.summarizer_agent)
        workflow.add_node("critic", self.critic_agent)
        workflow.add_node("refiner", self.refiner_agent)
        workflow.add_edge("researcher", "summarizer")
        workflow.add_edge("summarizer", "critic")
        workflow.add_conditional_edges("critic", self.should_continue, {"refiner": "refiner", END: END})
        workflow.add_edge("refiner", "critic")
        workflow.set_entry_point("researcher")
        return workflow.compile()

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self.build_graph()
        return self._graph

    def research_agent(self, state: ResearchState) -> ResearchState:
        try:
            from duckduckgo_search import DDGS
            query = state["user_query"]
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=8))
                state["research_data"] = "\n\n".join(r.get("body", "") for r in results)
                logger.info(f"Search completed for: {query[:80]}")
        except Exception as e:
            state["research_data"] = f"Search error: {e}"
            logger.error(f"Search failed: {e}")
        return state

    def summarizer_agent(self, state: ResearchState) -> ResearchState:
        system_prompt = "You are a skilled summarizer. Create a concise, comprehensive summary focusing on key points."
        research_data = state["research_data"]
        try:
            llm = self._get_llm(temperature=settings.LLM_TEMPERATURE)
            if llm:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Research: {research_data}\n\nQuery: {state['user_query']}")
                ]
                response = llm.invoke(messages)
                state["summary"] = response.content
                logger.info("Summary generated via LLM")
            else:
                state["summary"] = research_data[:1500]
        except Exception as e:
            state["summary"] = f"Summary error: {e}"
            logger.error(f"Summary failed: {e}")
        return state

    def critic_agent(self, state: ResearchState) -> ResearchState:
        system_prompt = (
            "You are a critical evaluator. Assess the summary on:\n"
            "1. Relevance to the query\n2. Completeness\n3. Accuracy\n4. Readability\n\n"
            "Provide a 1-10 score and feedback."
        )
        try:
            llm = self._get_llm(temperature=0.3)
            if llm:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Query: {state['user_query']}\n\nSummary:\n{state['summary']}")
                ]
                response = llm.invoke(messages)
                state["critique"] = response.content
                import re
                m = re.search(r"(\d+)/10|score:?\s*(\d+)", response.content, re.I)
                state["critique_score"] = int(m.group(1) or m.group(2)) if m else 5
                logger.info(f"Critique score: {state['critique_score']}")
            else:
                state["critique"] = "Auto-critique: LLM unavailable; assuming passing quality"
                state["critique_score"] = self.critique_threshold
        except Exception as e:
            state["critique"] = f"Critique error: {e}"
            state["critique_score"] = 5
            logger.error(f"Critique failed: {e}")
        return state

    def refiner_agent(self, state: ResearchState) -> ResearchState:
        state["iteration"] = state.get("iteration", 0) + 1
        logger.info(f"Refining output (iteration {state['iteration']})")

        system_prompt = "You are a refinement specialist. Improve the summary based on the critique while staying concise."
        try:
            llm = self._get_llm(temperature=0.5)
            if llm:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Original:\n{state['summary']}\n\nCritique:\n{state['critique']}\n\nQuery: {state['user_query']}")
                ]
                response = llm.invoke(messages)
                state["refined_output"] = response.content
                logger.info("Refinement completed via LLM")
            else:
                state["refined_output"] = state["summary"]
        except Exception as e:
            state["refined_output"] = f"Refinement error: {e}"
            logger.error(f"Refinement failed: {e}")
        return state

    def should_continue(self, state: ResearchState):
        current_iter = state.get("iteration", 0)
        max_iter = state.get("max_iterations", 3)
        score = state.get("critique_score", 0)

        logger.info(f"should_continue: iteration={current_iter}, max={max_iter}, score={score}, threshold={self.critique_threshold}")

        if current_iter >= max_iter:
            logger.info("Max iterations reached, ending")
            return END
        if score >= self.critique_threshold:
            logger.info(f"Critique threshold met ({score} >= {self.critique_threshold}), ending")
            return END
        return "refiner"

    def run(self, user_query: str) -> Dict[str, Any]:
        initial_state: ResearchState = {
            "user_query": user_query,
            "research_data": "",
            "summary": "",
            "critique": "",
            "refined_output": "",
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "critique_score": 0,
        }
        try:
            final_state = self.graph.invoke(initial_state)
            logger.info("Workflow completed successfully")
            return final_state
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise


orchestrator = WorkflowOrchestrator()
# Marble — Automated Document Q&A Pipeline

Extract text from PDFs, save as `.txt` files, and ask questions using LangGraph + Groq/Mistral LLMs. Everything runs locally — you just need API keys.

## How to Run

### 1. Setup

```bash
# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows
pip install -r requirements.txt

# Add your API keys
cp .env.example .env
# Edit .env — set GROQ_API_KEY and/or MISTRAL_API_KEY
```

### 2. Place your PDFs

Put your PDF files into the `uploads/` folder.

### 3. Run the automated pipeline

```bash
python run.py
```

This single command:
1. Extracts all PDFs to `.txt` files in `uploads/`
2. Starts the FastAPI server
3. Asks 6 pre-defined questions (3 per document)
4. Saves all Q&A results to `qa_results.json`
5. Shuts down the server

### 4. Or use the API manually

```bash
# Start the server
uvicorn main:app --reload --port 8000

# Ask a question (reads from .txt files in uploads/)
curl -X POST http://localhost:8000/research \
  -H 'Content-Type: application/json' \
  -d '{"query": "What ML models are compared?"}'

# View all research sessions
curl http://localhost:8000/sessions

# Get session details
curl http://localhost:8000/sessions/1
```

### 5. Run tests

```bash
pytest tests/ -v
```

## How It Works

The workflow reads `.txt` files directly from `uploads/`, so you only need to have `.txt` files there — no database setup required.

```
run.py                     Automated CLI (extract → ask → save)
main.py                    FastAPI server
workflow.py                LangGraph: read .txt files → LLM answer
prompts.py                 All LLM prompts (edit here to change AI behavior)
extract.py                 PDF → text conversion (PyMuPDF)
question_generator.py      Auto-generate suggested questions from .txt files
models.py                  SQLAlchemy models (Document, ResearchSession, AgentStep)
crud.py                    Database CRUD
database.py                SQLite engine
config.py                  Settings from .env
```

## LLM Prompts

All prompts sent to the AI are in **`prompts.py`** — edit this file to change how the model behaves.

Current system prompt:
```
You are a research assistant. Answer the user's question using ONLY
the document context provided below. If the answer is not in the
context, say you couldn't find it in the available documents.
```

The document context is appended after this prompt before being sent to the LLM.

## Q&A Results

All answers come directly from the `.txt` files in `uploads/` — no external data.

Source files: [RetinaDx GitHub Assets](https://github.com/nayaksomkar/RetinaDx/tree/main/assets)

- `RetinaDxGit.pdf` → `RetinaDxGit.txt`
- `RetinaDxPPT.pdf` → `RetinaDxPPT.txt`

### RetinaDxGit.txt (3 questions)

**Q1: What machine learning and deep learning models are compared for retinal disease detection?**

Machine Learning Models: Decision Tree, Random Forest, KNN. Deep Learning Models: DenseNet121, ResNet101, ResNet50.

**Q2: Which model achieved the highest accuracy and what was it?**

ResNet50 achieved the highest overall accuracy of 96.22%.

**Q3: What challenges exist in rural India for retina diagnosis according to the abstract?**

Distant medical facilities and specialist shortages make retina diagnosis expensive and inaccessible for villagers.

### RetinaDxPPT.txt (3 questions)

**Q1: What specific retinal diseases are focused on in this project?**

Cataract, Diabetic Retinopathy, and Glaucoma.

**Q2: What is a fundus image and how is it captured?**

A fundus image is a detailed photo of the back of the eye (retina, macula, optic disc), captured using a special fundus camera.

**Q3: According to the abstract, why is early and accurate screening important?**

Early and accurate screening is essential to prevent vision loss.

## Suggested Questions (Auto-Generated)

Run `python question_generator.py` to generate fresh questions from any .txt file in uploads/.

### From RetinaDxGit.txt

1. **What was the highest overall accuracy achieved by any ML model?**  
   ResNet50 reached 96.22%.

2. **Which classical ML algorithm achieved the highest accuracy?**  
   KNN peaked at 84.95%.

3. **What is the primary benefit of deep learning models for retinal disease detection?**  
   Higher precision, recall, specificity, and F1 scores — fewer false positives/negatives.

### From RetinaDxPPT.txt

1. **What retinal diseases are focused on?**  
   Cataract, Diabetic Retinopathy, and Glaucoma.

2. **What type of images are used to train the models?**  
   Fundus images — detailed photos of the back of the eye.

3. **What does the literature review say about deep learning in medical imaging?**  
   Deep learning, especially CNNs, often outperforms traditional ML in classification accuracy.


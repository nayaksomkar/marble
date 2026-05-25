"""
Generate suggested questions from .txt files in uploads/ using the LLM.
Usage:  python question_generator.py
"""
import json, os, sys
from pathlib import Path
from workflow import run_workflow

UPLOADS = Path("./uploads")
OUTPUT = Path("./suggested_questions.json")


def main():
    txt_files = sorted(UPLOADS.glob("*.txt"))
    if not txt_files:
        print("No .txt files found in uploads/")
        sys.exit(1)

    all_questions = {}

    for tf in txt_files:
        name = tf.stem
        print(f"\n--- {tf.name} ---")

        query = (
            f"Based on the document '{tf.name}', suggest 3 specific questions "
            "that a reader could ask about this document's content. "
            "Each question must be answerable using only the text provided. "
            "Return them as a numbered list."
        )

        result = run_workflow(query=query)
        answer = result.get("answer", "")
        print(answer)

        all_questions[name] = {
            "file": tf.name,
            "questions": answer,
        }

    with open(OUTPUT, "w") as f:
        json.dump(all_questions, f, indent=2)
    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()
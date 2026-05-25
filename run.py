"""
CLI entry point — fully automated workflow.
Usage:  python run.py
"""
import subprocess, sys, os, time, json, signal

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE, "uploads")

QUESTIONS_GIT = [
    "What machine learning and deep learning models are compared for retinal disease detection?",
    "Which model achieved the highest accuracy and what was it?",
    "What challenges exist in rural India for retina diagnosis according to the abstract?",
]
QUESTIONS_PPT = [
    "What specific retinal diseases are focused on in this project?",
    "What is a fundus image and how is it captured?",
    "According to the abstract, why is early and accurate screening important?",
]


def sh(cmd, **kw):
    print(f"\n  $ {cmd}")
    kw.setdefault("shell", True)
    kw.setdefault("cwd", BASE)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        print(r.stderr)
    return r


def wait_for_server(url="http://localhost:8000/health", timeout=30):
    import urllib.request
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    print("=" * 60)
    print("  MARBLE — Automated Document Q&A Pipeline")
    print("=" * 60)

    # 1. Extract PDFs → .txt in uploads/
    print("\n[1/6] Extracting PDFs to uploads/ ...")
    import fitz
    for fname in ["RetinaDxGit.pdf", "RetinaDxPPT.pdf"]:
        path = os.path.join(UPLOADS, fname)
        if not os.path.exists(path):
            print(f"  SKIP: {fname} not found")
            continue
        doc = fitz.open(path)
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        txtname = fname.replace(".pdf", ".txt")
        with open(os.path.join(UPLOADS, txtname), "w") as f:
            f.write(text)
        print(f"  ✓ {txtname} ({len(text)} chars)")

    # 2. Start server
    print("\n[2/6] Starting server ...")
    kill_port = subprocess.run(
        "fuser -k 8000/tcp 2>/dev/null; sleep 1", shell=True, capture_output=True
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not wait_for_server():
        print("  ✗ Server failed to start")
        proc.kill()
        sys.exit(1)
    print("  ✓ Server running on http://localhost:8000")

    # 3. Ask questions (reads directly from .txt files in uploads/)
    print("\n[3/6] Asking 6 questions (this may take a minute) ...")

    def ask(query):
        import urllib.request
        data = json.dumps({"query": query}).encode()
        req = urllib.request.Request(
            "http://localhost:8000/research", data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req).read())
        return resp.get("output", "")

    all_results = {"RetinaDxGit": {}, "RetinaDxPPT": {}}

    print("\n  --- RetinaDxGit Questions ---")
    for i, q in enumerate(QUESTIONS_GIT, 1):
        print(f"\n  Q{i}: {q}")
        ans = ask(q)
        all_results["RetinaDxGit"][f"Q{i}"] = {"question": q, "answer": ans[:500]}
        print(f"  A: {ans[:400]}")

    print("\n  --- RetinaDxPPT Questions ---")
    for i, q in enumerate(QUESTIONS_PPT, 1):
        print(f"\n  Q{i}: {q}")
        ans = ask(q)
        all_results["RetinaDxPPT"][f"Q{i}"] = {"question": q, "answer": ans[:500]}
        print(f"  A: {ans[:400]}")

    # 4. Save results
    print("\n[4/6] Saving results ...")
    with open(os.path.join(BASE, "qa_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print("  ✓ qa_results.json saved")

    # 5. Cleanup
    print("\n[5/6] Shutting down server ...")
    proc.terminate()
    proc.wait()

    print("\n" + "=" * 60)
    print("  DONE. Run 'python run.py' again to repeat.")
    print("  See README.md for full Q&A results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
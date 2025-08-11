# ADGM Corporate Agent (Document Intelligence)

A minimal Streamlit-based AI assistant that:
- Accepts `.docx` uploads
- Classifies document type
- Verifies required checklist for ADGM processes (Company Incorporation, Licensing)
- Detects red flags and inserts inline review comments into the `.docx`
- Uses simple local RAG over reference notes; optionally calls an LLM for clause suggestions
- Outputs a downloadable reviewed `.docx` and a structured JSON report

## Quickstart

1. Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. (Optional) Set OpenAI for suggestions:

```bash
setx OPENAI_API_KEY "your_api_key_here"
setx OPENAI_MODEL "gpt-4o-mini"
```

3. Run the app:

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Usage

- Upload one or more `.docx` files
- Review the detected document types
- Confirm or change the inferred process (e.g., Company Incorporation)
- Review checklist results and issues
- Download the reviewed `.docx` files and JSON report

## Reference Data (RAG)

Place your ADGM reference notes in `data/reference/*.txt` or `*.md`. A simple TF-IDF retriever surfaces the most relevant notes per issue.

## Example Files

- Add an example source `.docx` and the corresponding reviewed version into `examples/` after running the app for demo purposes.

## Submission Checklist

- GitHub repository or zip this folder
- Include one example docx before/after review in `examples/`
- Include the generated JSON report
- Include a screenshot of the UI

## Notes

- Comment insertion in `.docx` is implemented with low-level XML and may vary across document templates. If a paragraph match is not found, a comment is added at the beginning of the document. If your environment does not support Word comments, the app falls back to inserting reviewer-note paragraphs.
- Heuristics are conservative; extend rules in `corporate_agent/red_flags.py` and add more checklist items in `corporate_agent/checklists.py`.
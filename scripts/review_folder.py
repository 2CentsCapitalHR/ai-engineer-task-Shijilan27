import io
import json
from pathlib import Path
from typing import Dict, List

import typer
from docx import Document

from corporate_agent.doc_parser import extract_full_text
from corporate_agent.doc_classifier import classify_document_type
from corporate_agent.red_flags import detect_red_flags
from corporate_agent.docx_commenter import build_reviewed_docx
from corporate_agent.checklists import infer_process_from_documents, REQUIRED_DOCUMENTS_BY_PROCESS
from corporate_agent.rag import Retriever
from corporate_agent.report import build_report_dict


app = typer.Typer()


@app.command()
def review(folder: str, out: str = "out") -> None:
    folder_path = Path(folder)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    retriever = Retriever(reference_dir="data/reference")

    doc_texts: Dict[str, str] = {}
    doc_types: Dict[str, str] = {}
    for file in folder_path.glob("*.docx"):
        doc = Document(str(file))
        text = extract_full_text(doc)
        doc_texts[file.name] = text
        doc_types[file.name] = classify_document_type(text)

    inferred = infer_process_from_documents(list(doc_types.values()))
    required = REQUIRED_DOCUMENTS_BY_PROCESS.get(inferred, [])
    present = set(doc_types.values())
    missing = [r for r in required if r not in present]

    all_issues: List[Dict] = []
    for name, text in doc_texts.items():
        dtype = doc_types.get(name, "Unknown")
        issues = detect_red_flags(dtype, text)
        for issue in issues:
            refs = retriever.search(query=issue.get("issue", "") + " ADGM")
            issue["references"] = refs
            issue["document"] = dtype
            issue["file_name"] = name
        all_issues.extend(issues)

    report = build_report_dict(
        process=inferred,
        doc_types=doc_types,
        required_docs=required,
        missing_docs=missing,
        issues=all_issues,
    )
    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    for file in folder_path.glob("*.docx"):
        doc = Document(str(file))
        issues_for_file = [i for i in all_issues if i.get("file_name") == file.name]
        reviewed = build_reviewed_docx(doc, issues_for_file)
        reviewed.save(out_dir / f"{file.stem}__reviewed.docx")

    print(f"Report and reviewed docs saved to {out_dir.resolve()}")


if __name__ == "__main__":
    app()


import io
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

import streamlit as st

from corporate_agent.checklists import infer_process_from_documents, REQUIRED_DOCUMENTS_BY_PROCESS
from corporate_agent.doc_parser import load_docx_from_bytes, extract_full_text
from corporate_agent.doc_classifier import classify_document_type
from corporate_agent.red_flags import detect_red_flags
from corporate_agent.docx_commenter import build_reviewed_docx
from corporate_agent.rag import Retriever
from corporate_agent.sources import fetch_urls
from corporate_agent.llm import ClauseSuggester
from corporate_agent.report import build_report_dict


st.set_page_config(page_title="ADGM Corporate Agent", layout="wide")
st.title("ADGM-Compliant Corporate Agent with Document Intelligence")
st.caption("Upload .docx files for review against ADGM requirements. The app will flag issues, insert inline reviewer notes, and generate a structured report.")


@st.cache_resource
def get_retriever() -> Retriever:
    return Retriever(reference_dir="data/reference")


@st.cache_resource
def get_suggester() -> ClauseSuggester:
    return ClauseSuggester()


def main() -> None:
    retriever = get_retriever()
    suggester = get_suggester()

    uploaded_files = st.file_uploader(
        "Upload one or more .docx files",
        type=["docx"],
        accept_multiple_files=True,
        help="The agent will parse and analyze these documents.",
    )

    with st.expander("Optional: Add official ADGM links to ground checks"):
        urls_text = st.text_area(
            "Paste one URL per line (HTML, PDF, or DOCX)",
            value="",
            placeholder="https://www.adgm.com/operating-in-adgm/registration-authority\nhttps://assets.adgm.com/download/...",
            height=120,
        )
        if st.button("Fetch & Index Links"):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            if urls:
                with st.spinner("Fetching and indexing..."):
                    extra_docs = fetch_urls(urls, save_dir="data/external")
                    retriever.extend_with(extra_docs)
                st.success(f"Indexed {len(extra_docs)} documents from URLs.")

    if not uploaded_files:
        st.info("Awaiting files. Upload .docx to begin.")
        st.stop()

    # Parse and classify each uploaded document
    doc_texts: Dict[str, str] = {}
    doc_types: Dict[str, str] = {}
    for up in uploaded_files:
        try:
            doc = load_docx_from_bytes(up.read())
            text = extract_full_text(doc)
            doc_texts[up.name] = text
            doc_types[up.name] = classify_document_type(text)
        except Exception as exc:
            st.error(f"Failed to parse {up.name}: {exc}")

    with st.expander("Detected Document Types", expanded=True):
        for name, dtype in doc_types.items():
            st.write(f"- {name}: {dtype}")

    # Infer the legal process
    inferred_process = infer_process_from_documents(list(doc_types.values()))
    process = st.selectbox(
        "Detected process (you can override)",
        options=list(REQUIRED_DOCUMENTS_BY_PROCESS.keys()),
        index=list(REQUIRED_DOCUMENTS_BY_PROCESS.keys()).index(inferred_process)
        if inferred_process in REQUIRED_DOCUMENTS_BY_PROCESS
        else 0,
    )

    # Checklist verification
    required = REQUIRED_DOCUMENTS_BY_PROCESS.get(process, [])
    present_types = set(doc_types.values())
    missing = [req for req in required if req not in present_types]

    st.subheader("Checklist Verification")
    st.write(
        f"It appears that you're trying to {process.lower()}. Based on our reference list, "
        f"you have uploaded {len(present_types)} out of {len(required)} required documents."
    )
    if missing:
        st.error("Missing required documents: " + ", ".join(missing))
    else:
        st.success("All required documents are present.")

    # Analyze red flags and suggestions
    all_issues: List[Dict] = []
    st.subheader("Document Analysis")
    for name, text in doc_texts.items():
        dtype = doc_types.get(name, "Unknown")
        issues = detect_red_flags(dtype, text)

        # Retrieve supporting references and suggest fixes (optional)
        for issue in issues:
            query = issue.get("issue", "") + " " + dtype + " ADGM"
            refs = retriever.search(query=query, top_k=3)
            issue["references"] = refs
            suggestion = suggester.suggest(issue=issue, references=refs)
            if suggestion:
                issue["suggestion"] = suggestion
            issue["document"] = dtype
            issue["file_name"] = name
        all_issues.extend(issues)

        # Show issues in UI
        with st.expander(f"Issues in {name} ({dtype})", expanded=False):
            if not issues:
                st.write("No issues found by heuristic checks.")
            else:
                for i, iss in enumerate(issues, start=1):
                    st.write(f"{i}. Section: {iss.get('section', 'N/A')} | Severity: {iss.get('severity', 'Medium')}")
                    st.write(f"Issue: {iss.get('issue')}")
                    if iss.get("suggestion"):
                        st.write(f"Suggestion: {iss['suggestion']}")
                    if iss.get("references"):
                        for ref in iss["references"]:
                            st.write(f"- Ref: {ref['title']} ({ref['source']})")

    # Build report dict
    report_dict = build_report_dict(
        process=process,
        doc_types=doc_types,
        required_docs=required,
        missing_docs=missing,
        issues=all_issues,
    )

    st.subheader("Structured Output")
    st.json(report_dict)

    # Generate reviewed files for download
    st.subheader("Reviewed Documents")
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    for up in uploaded_files:
        up_bytes = up.getvalue()
        doc = load_docx_from_bytes(up_bytes)
        issues_for_file = [i for i in all_issues if i.get("file_name") == up.name]
        reviewed_doc = build_reviewed_docx(doc, issues_for_file)

        out_bytes = io.BytesIO()
        reviewed_doc.save(out_bytes)
        out_bytes.seek(0)
        download_name = f"{os.path.splitext(up.name)[0]}__reviewed__{timestamp}.docx"
        st.download_button(
            label=f"Download reviewed: {download_name}",
            data=out_bytes.getvalue(),
            file_name=download_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # Download structured report
    report_bytes = io.BytesIO(json.dumps(report_dict, indent=2).encode("utf-8"))
    st.download_button(
        label="Download structured report (JSON)",
        data=report_bytes.getvalue(),
        file_name=f"adgm_corporate_agent_report_{timestamp}.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()


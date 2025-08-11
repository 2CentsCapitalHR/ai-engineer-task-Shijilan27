from typing import Dict, List


def build_report_dict(
    process: str,
    doc_types: Dict[str, str],
    required_docs: List[str],
    missing_docs: List[str],
    issues: List[Dict],
) -> Dict:
    return {
        "process": process,
        "documents_uploaded": len(set(doc_types.values())),
        "required_documents": len(required_docs),
        "missing_documents": missing_docs,
        "issues_found": issues,
    }


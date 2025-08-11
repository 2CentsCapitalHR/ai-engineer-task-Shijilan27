from typing import Dict, List


# Minimal initial checklist; can be expanded with more processes
REQUIRED_DOCUMENTS_BY_PROCESS: Dict[str, List[str]] = {
    "Company Incorporation": [
        "Articles of Association",
        "Memorandum of Association",
        "Board Resolution",
        "Shareholder Resolution",
        "Incorporation Application",
        "UBO Declaration",
        "Register of Members and Directors",
    ],
    "Licensing": [
        "License Application",
        "Board Resolution",
        "Shareholder Resolution",
    ],
}


DOCUMENT_TYPE_ALIASES: Dict[str, List[str]] = {
    "Articles of Association": ["AoA", "Articles"],
    "Memorandum of Association": ["MoA", "MoU", "Memorandum"],
    "Board Resolution": ["BR", "Board Resolution Template"],
    "Shareholder Resolution": ["SR", "Shareholder Resolution Template"],
    "Incorporation Application": ["Application Form", "Incorporation Form"],
    "UBO Declaration": ["UBO", "Ultimate Beneficial Owner Declaration"],
    "Register of Members and Directors": ["Register of Members", "Register of Directors"],
    "Change of Registered Address Notice": ["Change of Address"],
    "License Application": ["Licensing Application"],
}


def normalize_type_label(label: str) -> str:
    label = label.strip()
    for canonical, aliases in DOCUMENT_TYPE_ALIASES.items():
        if label == canonical:
            return canonical
        if any(label.lower() == a.lower() for a in aliases):
            return canonical
    return label


def infer_process_from_documents(detected_types: List[str]) -> str:
    normalized = [normalize_type_label(t) for t in detected_types]
    score = {
        "Company Incorporation": 0,
        "Licensing": 0,
    }
    for t in normalized:
        if t in REQUIRED_DOCUMENTS_BY_PROCESS["Company Incorporation"]:
            score["Company Incorporation"] += 1
        if t in REQUIRED_DOCUMENTS_BY_PROCESS["Licensing"]:
            score["Licensing"] += 1
    # Default to Incorporation if tie or empty
    if score["Licensing"] > score["Company Incorporation"]:
        return "Licensing"
    return "Company Incorporation"


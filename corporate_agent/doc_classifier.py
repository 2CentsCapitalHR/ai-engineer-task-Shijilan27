from typing import List


KEYWORDS = {
    "Articles of Association": ["articles of association", "aoa"],
    "Memorandum of Association": ["memorandum of association", "moa", "mou"],
    "Board Resolution": ["board resolution"],
    "Shareholder Resolution": ["shareholder resolution"],
    "Incorporation Application": ["incorporation application", "application form"],
    "UBO Declaration": ["ubo", "beneficial owner"],
    "Register of Members and Directors": ["register of members", "register of directors"],
    "Change of Registered Address Notice": ["change of registered address"],
    "License Application": ["licensing application", "license application"],
}


def classify_document_type(text: str) -> str:
    lowered = text.lower()
    for label, phrases in KEYWORDS.items():
        for p in phrases:
            if p in lowered:
                return label
    # fallback heuristic
    if "articles" in lowered and "association" in lowered:
        return "Articles of Association"
    if "memorandum" in lowered:
        return "Memorandum of Association"
    return "Unknown"


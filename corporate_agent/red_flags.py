from typing import Dict, List


def detect_red_flags(document_type: str, text: str) -> List[Dict]:
    issues: List[Dict] = []
    lowered = text.lower()

    # Jurisdiction check
    if "adgm" not in lowered:
        issues.append({
            "section": "Jurisdiction",
            "issue": "Jurisdiction clause does not specify ADGM",
            "severity": "High",
        })

    # Ambiguous language
    ambiguous_terms = ["should", "may", "seeks to", "aims to"]
    if any(term in lowered for term in ambiguous_terms):
        issues.append({
            "section": "Binding Language",
            "issue": "Ambiguous or non-binding language detected",
            "severity": "Medium",
        })

    # Missing signatory
    signatory_cues = ["signature", "signatory", "signed by", "authorised signatory", "date"]
    if not any(cue in lowered for cue in signatory_cues):
        issues.append({
            "section": "Execution",
            "issue": "Missing signatory/execution section",
            "severity": "High",
        })

    # Formatting cues
    if len(text.strip()) < 300:
        issues.append({
            "section": "Formatting",
            "issue": "Document appears unusually short; check template completeness",
            "severity": "Low",
        })

    # ADGM-specific template hints by type
    if document_type == "Articles of Association":
        if "share capital" not in lowered:
            issues.append({
                "section": "Capital",
                "issue": "AoA missing reference to share capital",
                "severity": "Medium",
            })

    return issues


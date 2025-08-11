import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


class ClauseSuggester:
    def __init__(self) -> None:
        # Placeholder: try to use OpenAI if key provided; otherwise return heuristic suggestions
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        try:
            if self.api_key:
                from openai import OpenAI  # type: ignore

                self.client = OpenAI(api_key=self.api_key)
            else:
                self.client = None
        except Exception:
            self.client = None

    def suggest(self, issue: Dict, references: List[Dict]) -> Optional[str]:
        prompt = (
            "Provide a concise, ADGM-aligned clause suggestion to address the following issue.\n"
            f"Issue: {issue.get('issue')}\n"
            f"Document Type: {issue.get('document')}\n"
            f"References: {', '.join([r.get('title','') for r in references])}.\n"
            "Respond in one or two sentences."
        )
        if not self.client:
            # Heuristic fallback
            if "Jurisdiction" in issue.get("section", ""):
                return "Specify that disputes are subject to ADGM Courts jurisdiction and governed by ADGM Regulations."
            if "Binding Language" in issue.get("section", ""):
                return "Replace ambiguous terms with mandatory language (e.g., 'shall' instead of 'may')."
            return None

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ADGM compliance assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=120,
            )
            return resp.choices[0].message.content if resp.choices else None
        except Exception:
            return None


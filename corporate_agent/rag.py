import os
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ReferenceDoc:
    title: str
    text: str
    source: str


class Retriever:
    def __init__(self, reference_dir: str) -> None:
        self.reference_dir = reference_dir
        self.docs: List[ReferenceDoc] = self._load_references(reference_dir)
        corpus = [d.text for d in self.docs]
        if not corpus:
            corpus = [""]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _load_references(self, ref_dir: str) -> List[ReferenceDoc]:
        docs: List[ReferenceDoc] = []
        if not os.path.isdir(ref_dir):
            return docs
        for name in os.listdir(ref_dir):
            path = os.path.join(ref_dir, name)
            if not os.path.isfile(path):
                continue
            if not name.lower().endswith((".txt", ".md")):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                docs.append(ReferenceDoc(title=os.path.splitext(name)[0], text=text, source=path))
            except Exception:
                continue
        return docs

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self.docs:
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        top_idx = np.argsort(-sims)[:top_k]
        results: List[Dict] = []
        for i in top_idx:
            d = self.docs[int(i)]
            snippet = d.text[:240].replace("\n", " ")
            results.append({
                "title": d.title,
                "source": d.source,
                "score": float(sims[int(i)]),
                "snippet": snippet,
            })
        return results

    def extend_with(self, extra: List[Dict]) -> None:
        # Add extra reference docs dynamically (e.g., from URLs)
        for e in extra:
            title = e.get("title", "External")
            text = e.get("text", "")
            source = e.get("source", "")
            if not text:
                continue
            self.docs.append(ReferenceDoc(title=title, text=text, source=source))
        corpus = [d.text for d in self.docs] or [""]
        self.matrix = self.vectorizer.fit_transform(corpus)


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .nlp_backends import _embed
from .parse import normalize


@dataclass
class RankedBullet:
    text: str
    score: float  # cosine similarity, bounded in [0, 1]

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "score": float(self.score)}


def _split_resume_into_bullets(resume_text: str) -> List[str]:
    """
    Heuristic splitter: turn raw resume text into bullet-like lines.

    - splits on newlines and inline "•"
    - strips bullet markers
    - keeps lines of reasonable length (30 to 500 chars)
    - de-duplicates by normalised text
    - filters out section headers, contact info, summaries, education entries,
      date/job title header lines, and comma-separated skill lists
    """
    import re

    raw: List[str] = []

    # Action verbs commonly found in real achievement bullets
    action_verbs = {
        "built", "developed", "created", "designed", "implemented", "engineered",
        "optimized", "improved", "reduced", "increased", "automated", "led",
        "managed", "delivered", "launched", "architected", "deployed", "scaled",
        "analyzed", "spearheaded", "orchestrated", "transformed", "established",
        "crafted", "modeled", "trained", "integrated", "produced", "maintained",
    }

    # Patterns to skip (headers, contact info, summaries, education, date lines)
    skip_patterns = [
        r"^(summary|objective|profile|about|experience|education|skills|projects|certifications|publications|awards)\s*:?\s*$",
        r"^(email|phone|linkedin|github|portfolio|location|address)\s*:?\s*",
        r"^\s*[\-\•\*]\s*(summary|objective|profile|about)\s*",
        r"@",
        r"(university|college|institute|bachelor|master|phd|mba|degree|graduated)",
        r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b",  # date ranges like "2019-2021" anywhere in line
        r"\b(19|20)\d{2}\s*[-–]\s*(present|current)\b",  # date ranges like "2021-Present"
        r"^\s*[\-\•\*]\s*$",  # empty bullets
        r"^(languages|tools|technologies|frameworks|databases|skills|core competencies)\s*:.*",
        r"\b(experienced|passionate|results-driven|motivated|dedicated|innovative)\b.*?\b(engineer|developer|scientist|analyst|manager|professional|specialist)\b",
    ]
    skip_re = re.compile("|".join(skip_patterns), re.IGNORECASE)

    def is_skill_list(line: str) -> bool:
        """Filter out comma-separated skill lists like 'Python, PyTorch, SQL, Docker'."""
        items = [i.strip() for i in line.split(",") if i.strip()]
        if len(items) >= 4:
            low_line = line.lower()
            if not any(v in low_line for v in action_verbs):
                return True
        return False

    for line in resume_text.splitlines():
        ln = line.strip()
        if not ln:
            continue

        # Skip headers, non-bullet content, and skill lists
        if skip_re.search(ln) or is_skill_list(ln):
            continue

        # Split lines that contain multiple bullet separators, e.g., "• foo • bar"
        if "•" in ln[1:]:
            parts = [p.strip(" •\t-–*") for p in ln.split("•")]
            for p in parts:
                if p and len(p) >= 20 and not is_skill_list(p):
                    raw.append(p)
        else:
            # Standard single bullet or sentence line
            cleaned = ln.lstrip("• \t-–*")
            if cleaned and len(cleaned) >= 20:
                raw.append(cleaned)

    # If we got very few bullets, try splitting on bullet/numbering patterns
    if len(raw) < 3:
        raw = []
        for line in resume_text.splitlines():
            ln = line.strip()
            if not ln:
                continue
            if skip_re.search(ln) or is_skill_list(ln):
                continue
            # Split on bullet markers, dashes, or numbered items
            if re.match(r"^[\-\•\*]\s+", ln) or re.match(r"^\d+[\.\)]\s+", ln):
                cleaned = re.sub(r"^[\-\•\*]\s+", "", ln)
                cleaned = re.sub(r"^\d+[\.\)]\s+", "", cleaned)
                if len(cleaned) >= 20:
                    raw.append(cleaned)
            elif len(ln) > 40:  # Long enough to be a meaningful bullet
                raw.append(ln)

    # Drop lines that are too short or too long to be useful
    candidates = [r for r in raw if 30 <= len(r) <= 500]

    # Remove duplicates while preserving order
    seen: set[str] = set()
    bullets: List[str] = []
    for b in candidates:
        nb = normalize(b)
        if not nb or nb in seen:
            continue
        seen.add(nb)
        bullets.append(b)

    return bullets


def _tfidf_similarity(jd_text: str, bullets: List[str]) -> List[float]:
    """Fallback TF-IDF cosine similarity when embeddings fail."""
    if not bullets:
        return []
    try:
        vec = TfidfVectorizer(min_df=1, stop_words="english", ngram_range=(1, 2))
        X = vec.fit_transform([jd_text] + bullets)
        sims = cosine_similarity(X[0:1], X[1:])[0]
        return [float(max(0.0, min(1.0, s))) for s in sims]
    except Exception:
        return [0.0] * len(bullets)


def compute_evidence_ranking(
    *,
    jd_text: str,
    resume_text: str,
    top_k: int = 5,
    bottom_k: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Rank resume bullets by semantic similarity to the JD.

    Returns a dict with:
      - all:   all bullets sorted by similarity (desc)
      - top:   top_k strongest bullets
      - bottom: bottom_k weakest bullets
    """
    jd_text = (jd_text or "").strip()
    if not jd_text:
        return {"all": [], "top": [], "bottom": []}

    bullets = _split_resume_into_bullets(resume_text or "")
    if not bullets:
        return {"all": [], "top": [], "bottom": []}

    # Try embeddings first
    scores = None
    try:
        embs = _embed([jd_text, *bullets])
        if embs is not None:
            arr = np.asarray(embs, dtype="float32")
            if arr.ndim == 2 and arr.shape[0] == len(bullets) + 1:
                jd_vec = arr[0:1, :]
                bullet_vecs = arr[1:, :]
                jd_norm = jd_vec / (np.linalg.norm(jd_vec, axis=1, keepdims=True) + 1e-8)
                b_norm = bullet_vecs / (np.linalg.norm(bullet_vecs, axis=1, keepdims=True) + 1e-8)
                sims = (jd_norm @ b_norm.T)[0]
                scores = np.clip(sims, 0.0, 1.0).tolist()
    except Exception:
        pass

    # Fallback to TF-IDF
    if scores is None:
        scores = _tfidf_similarity(jd_text, bullets)

    ranked: List[RankedBullet] = [
        RankedBullet(text=b, score=float(s)) for b, s in zip(bullets, scores, strict=False)
    ]
    ranked.sort(key=lambda rb: rb.score, reverse=True)

    top_k = max(0, min(top_k, len(ranked)))
    bottom_k = max(0, min(bottom_k, len(ranked)))

    top = ranked[:top_k]
    bottom = ranked[-bottom_k:] if bottom_k else []

    return {
        "all": [rb.to_dict() for rb in ranked],
        "top": [rb.to_dict() for rb in top],
        "bottom": [rb.to_dict() for rb in bottom],
    }

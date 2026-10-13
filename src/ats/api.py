# FastAPI application exposing the ATS analysis engine to the Next.js frontend.
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ats.evidence import compute_evidence_ranking
from ats.llm import score_fit_dimensions, suggest_resume_improvements
from ats.nlp_backends import (
    extract_jd_keywords_batch,
    present_missing_vs_resume,
)
from ats.parse import parse_job_description, parse_resume
from ats.pdf_utils import extract_text_auto, extract_text_from_pdf
from ats.prompts.prompts import build_make_edits_prompt
from ats.scoring import compute_score, compute_score_advanced

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ats_api")

USE_SEMANTIC = os.getenv("USE_SEMANTIC", "1").lower() not in ("0", "false", "no")
LLM_ENABLE = os.getenv("LLM_ENABLE", "1").lower() not in {"0", "", "false"}
LLM_MODEL = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")
MAX_FILE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

app = FastAPI(title="ResuMatch ATS API", version="0.2")

# Allow the Next.js dev server (and preview) to call this API.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3005",
    "http://127.0.0.1:3005",
    "http://localhost:8501",
]
if extra := os.getenv("CORS_ORIGINS"):
    ALLOWED_ORIGINS.extend([o.strip() for o in extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    fit_dimensions: dict
    simple_score: dict
    advanced_score: dict
    jd_keyword_groups: dict
    present_keywords: list[str]
    missing_keywords: list[str]
    evidence: dict
    suggestions: dict
    make_edits_prompt: str
    jd_title: Optional[str] = None
    jd_seniority: Optional[str] = None


def _mb(bytes_: int) -> float:
    return bytes_ / (1024 * 1024)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume: UploadFile = File(...),
    jd_text: str = Form(""),
    jd_file: Optional[UploadFile] = File(None),
    enable_ocr: bool = Form(True),
    max_pages: int = Form(5),
    llm_enable: bool = Form(True),
    llm_model: str = Form(LLM_MODEL),
):
    # --- Validate resume ---
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")
    rbytes = await resume.read()
    if _mb(len(rbytes)) > MAX_FILE_MB:
        raise HTTPException(status_code=413, detail=f"Resume exceeds {MAX_FILE_MB}MB limit.")

    # --- Resolve JD source (file takes precedence over pasted text) ---
    jd_bytes: Optional[bytes] = None
    if jd_file and jd_file.filename:
        jd_bytes = await jd_file.read()
        if _mb(len(jd_bytes)) > MAX_FILE_MB:
            raise HTTPException(status_code=413, detail="JD file exceeds size limit.")

    if jd_bytes:
        jd_text = extract_text_auto(
            jd_bytes,
            filename=jd_file.filename,
            enable_ocr=enable_ocr,
            ocr_lang="eng",
            max_pages=max_pages,
        )
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    # --- Extract resume text ---
    resume_text = extract_text_from_pdf(
        rbytes, enable_ocr=enable_ocr, ocr_lang="eng", max_pages=max_pages
    )
    resume_parsed = parse_resume(resume_text)
    jd_parsed = parse_job_description(jd_text)

    # --- 1) JD keywords + present/missing ---
    jd_batch = extract_jd_keywords_batch([jd_text])
    jd_cats = jd_batch[0] if jd_batch else {
        "tools": [], "methods": [], "competencies": [], "industry": [],
    }
    present_pm, missing_pm = present_missing_vs_resume(jd_cats, resume_text)

    # --- 2) Scoring ---
    adv = compute_score_advanced(
        jd_text=jd_text,
        resume_text=resume_text,
        resume_parsed=resume_parsed,
        use_semantic=USE_SEMANTIC,
    )
    adv_d = adv.to_dict()
    simple = compute_score(jd_text=jd_text, resume_text=resume_text)
    simple_d = simple.to_dict()

    # --- 3) Evidence ranking ---
    evidence = compute_evidence_ranking(
        jd_text=jd_text, resume_text=resume_text, top_k=5, bottom_k=5
    )

    # --- 4) Multi-dimensional fit ---
    dim_scores = score_fit_dimensions(
        jd_text=jd_text,
        resume_text=resume_text,
        present_keywords=adv_d["present_keywords"],
        missing_keywords=adv_d["missing_keywords"],
        model=llm_model,
        enable_llm=llm_enable and LLM_ENABLE,
    )

    # --- 5) Suggestions ---
    try:
        sugg = suggest_resume_improvements(
            jd_text=jd_text,
            resume_text=resume_text,
            missing_keywords=adv_d["missing_keywords"],
            present_keywords=adv_d["present_keywords"],
            enable_llm=llm_enable and LLM_ENABLE,
            model=llm_model,
            max_bullets=5,
        ).to_dict()
    except Exception as e:  # noqa: BLE001
        logger.warning("Suggestion generation failed: %s", e)
        sugg = {
            "missing_keywords": list(adv_d["missing_keywords"]),
            "tailored_bullets": [],
            "notes": "LLM unavailable",
        }

    make_edits_prompt = build_make_edits_prompt(
        jd_text=jd_text,
        present_keywords=adv.present_keywords,
        missing_keywords=adv.missing_keywords,
        tailored_bullets=(sugg.get("tailored_bullets") or None),
        resume_text=None,
        jd_keywords_categorized=jd_cats,
        industry_hint=None,
        role_title=jd_parsed.get("title"),
        deadline=None,
        role_type=None,
        seniority=jd_parsed.get("seniority"),
        focus=None,
        extras=None,
        include_raw=False,
    )

    return AnalyzeResponse(
        fit_dimensions=dim_scores.to_dict(),
        simple_score=simple_d,
        advanced_score=adv_d,
        jd_keyword_groups=jd_cats,
        present_keywords=present_pm,
        missing_keywords=missing_pm,
        evidence=evidence,
        suggestions=sugg,
        make_edits_prompt=make_edits_prompt,
        jd_title=jd_parsed.get("title"),
        jd_seniority=jd_parsed.get("seniority"),
    )

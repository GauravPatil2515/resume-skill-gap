from ats.scoring import compute_score, compute_score_advanced
from ats.parse import parse_resume

def test_compute_score_simple():
    jd = "Seeking a developer skilled in Python, SQL, and Docker."
    resume = "Experienced in Python and SQL with background in databases."
    res = compute_score(jd_text=jd, resume_text=resume)
    assert res.composite > 0
    assert "python" in res.present_keywords
    assert "docker" in res.missing_keywords
    assert res.keyword_coverage > 0

def test_compute_score_advanced():
    jd = """
    Software Engineer
    Required: Python, Docker, PostgreSQL
    Nice to have: Kubernetes
    """
    resume = """
    Software Developer
    Experience:
    • Engineered microservices using Python and Docker
    • Managed PostgreSQL databases for high availability
    """
    parsed_resume = parse_resume(resume)
    res = compute_score_advanced(
        jd_text=jd,
        resume_text=resume,
        resume_parsed=parsed_resume,
        use_semantic=False,
    )
    assert res.composite > 0
    assert "python" in res.present_keywords
    assert "docker" in res.present_keywords
    assert res.keyword_coverage > 0
    assert isinstance(res.to_dict(), dict)

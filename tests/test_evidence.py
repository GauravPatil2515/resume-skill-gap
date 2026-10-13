from ats.evidence import _split_resume_into_bullets, compute_evidence_ranking

def test_split_resume_into_bullets():
    resume = """
    John Doe
    john@example.com

    Experience:
    • Built real-time analytics pipeline processing 10M events daily using Kafka.
    • Architected cloud infrastructure on AWS reducing operational costs by 25%.
    - Designed and implemented RESTful APIs using Python and FastAPI.
    """
    bullets = _split_resume_into_bullets(resume)
    assert len(bullets) >= 2
    assert any("analytics" in b.lower() for b in bullets)

def test_compute_evidence_ranking():
    jd = "Looking for a cloud backend engineer who built scalable REST APIs in Python."
    resume = """
    • Designed and implemented RESTful APIs using Python and FastAPI.
    • Optimized database queries improving response times by 30%.
    • Managed physical warehouse inventory and catalogued hardware parts.
    """
    result = compute_evidence_ranking(jd_text=jd, resume_text=resume, top_k=2, bottom_k=1)
    assert "all" in result
    assert "top" in result
    assert "bottom" in result
    assert len(result["top"]) <= 2
    # The API bullet should be ranked high
    if result["top"]:
        top_text = result["top"][0]["text"].lower()
        assert "api" in top_text or "python" in top_text or "database" in top_text

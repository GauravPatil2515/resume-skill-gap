import pytest
from fastapi.testclient import TestClient
import fitz

from ats.api import app

def create_sample_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_analyze_requires_pdf(client):
    res = client.post(
        "/analyze",
        files={"resume": ("resume.txt", b"plain text", "text/plain")},
        data={"jd_text": "Python developer"}
    )
    assert res.status_code == 400
    assert "PDF" in res.json().get("detail", "")

def test_analyze_requires_jd(client):
    pdf = create_sample_pdf("Software Engineer with Python skills.")
    res = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", pdf, "application/pdf")},
        data={"jd_text": ""}
    )
    assert res.status_code == 400

def test_analyze_success(client):
    pdf_content = (
        "Senior Software Engineer\n"
        "Proficient in Python, PostgreSQL, Docker, and Git.\n"
        "• Developed scalable backend services handling high transaction volume.\n"
        "• Reduced query latencies by optimizing relational database schema."
    )
    pdf = create_sample_pdf(pdf_content)
    jd_content = (
        "Senior Software Engineer\n"
        "We are looking for a Python engineer skilled in PostgreSQL and Docker."
    )
    res = client.post(
        "/analyze",
        files={"resume": ("resume.pdf", pdf, "application/pdf")},
        data={
            "jd_text": jd_content,
            "llm_enable": "false"  # Test deterministic heuristic path
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "simple_score" in data
    assert "advanced_score" in data
    assert "present_keywords" in data
    assert "missing_keywords" in data
    assert "evidence" in data
    assert "make_edits_prompt" in data
    assert "python" in [k.lower() for k in data["present_keywords"]]

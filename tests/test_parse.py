from ats.parse import (
    extract_skills,
    extract_bullets,
    extract_seniority,
    parse_resume,
    parse_job_description,
    BASIC_SKILLS,
)

def test_extract_skills():
    text = "Proficient in Python, SQL, Docker, and PyTorch."
    skills = extract_skills(text, BASIC_SKILLS)
    assert "python" in skills
    assert "sql" in skills
    assert "docker" in skills
    assert "pytorch" in skills

def test_extract_seniority():
    assert extract_seniority("Senior Software Engineer required") == "senior"
    assert extract_seniority("Graduate Data Scientist position") == "graduate"
    assert extract_seniority("Junior Developer role") == "graduate"
    assert extract_seniority("General engineering role") is None

def test_extract_bullets():
    jd = """
    Responsibilities:
    - Build scalable backend APIs using FastAPI
    - Deploy containerized services to Kubernetes
    Requirements:
    • 3+ years experience with Python
    """
    bullets = extract_bullets(jd)
    assert len(bullets) >= 2
    assert any("FastAPI" in b or "fastapi" in b.lower() for b in bullets)

def test_parse_job_description():
    jd = """
    Senior Python Developer
    Responsibilities:
    - Develop backend microservices with Python and Docker
    - Maintain PostgreSQL databases
    Requirements:
    - Solid knowledge of Git and Linux
    """
    res = parse_job_description(jd)
    assert res["seniority"] == "senior"
    assert "python" in res["skills"]
    assert "docker" in res["skills"]
    assert len(res["bullets"]) >= 1

def test_parse_resume():
    resume_text = """
    Jane Doe
    jane.doe@example.com
    +1 555-0199

    Summary:
    Experienced engineer with a passion for high performance systems.

    Experience:
    Senior Engineer, TechCorp (2020 - Present)
    • Architected distributed systems in Python and Go
    • Reduced API latency by 40% with Redis caching

    Skills:
    Python, Go, Docker, Redis, Git, Linux
    """
    parsed = parse_resume(resume_text)
    assert parsed["basics"]["email"] == "jane.doe@example.com"
    assert "python" in parsed["skills"]
    assert "docker" in parsed["skills"]
    assert len(parsed["experience"]) >= 1

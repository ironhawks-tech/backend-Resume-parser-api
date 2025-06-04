import requests, os

def call_mistral(prompt: str) -> str:
    url = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434") + "/api/generate"

    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["response"]

def build_resume_prompt(resume_text: str) -> str:
    return f"""
You are a professional resume parser AI.

Given the following resume text, extract a structured JSON with these fields:
- name
- email
- phone
- skills (list)
- education (list of {{degree, institution, year}})
- experience (list of {{job_title, company, years}})
- role (IMPORTANT: From the skills and experience provided, list the most suitable job roles for this candidate as a JSON array of short role titles only. Do NOT include any descriptions or explanations, just the role names in an array. Example: ["Backend Developer", "Cloud Engineer"])

It should work for resumes across any domain — tech or non-tech, structured or unstructured.

Resume:
\"\"\"
{resume_text}
\"\"\"

Only output valid JSON.
"""

import re
from typing import Dict, List
from services.zero_shot_classifier import classify_chunks


SECTION_HEADERS = [
    "personal information", "contact information",
    "education", "experience", "work experience", "professional experience",
    "projects", "skills", "technical skills", "soft skills",
    "certifications", "certification",
    
]

INLINE_HEADERS = [
    "soft skills", "technical skills",
    "certifications", "certification",
   
]

HEADER_PATTERN = re.compile(
    r"(?P<header>" + "|".join(SECTION_HEADERS) + r")\s*[:\-]?\s*$",
    re.IGNORECASE | re.MULTILINE
)

INLINE_HEADER_PATTERN = re.compile(
    r"(?P<header>" + "|".join(INLINE_HEADERS) + r")\s*[:\-]",
    re.IGNORECASE
)

def clean_resume_text(text: str) -> str:
    """
    Preprocess the resume text:
    - Normalize whitespace
    - Remove extra newlines
    - Replace bullet points
    - Remove long dash/underscore dividers
    """
    # Replace bullet symbols with dashes
    text = re.sub(r'[•●▪◦‣]', '-', text)

    # Normalize multiple newlines to max 2
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    # Remove excessive dashes, underscores, or equals used as dividers
    text = re.sub(r'[-=_]{3,}', '', text)

    # Normalize spaces and tabs
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove leading/trailing whitespace
    return text.strip()


def regex_segment(text: str) -> Dict[str, str]:
    sections = {}
    matches = list(HEADER_PATTERN.finditer(text))

    for i, match in enumerate(matches):
        section_name = match.group("header").strip().lower()
        section_start = match.end()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[section_start:section_end].strip()
        if section_name not in sections:
            sections[section_name] = content

    inline_matches = list(INLINE_HEADER_PATTERN.finditer(text))
    for i, match in enumerate(inline_matches):
        inline_header = match.group("header").strip().lower()
        start = match.end()
        end = inline_matches[i + 1].start() if i + 1 < len(inline_matches) else len(text)
        content = text[start:end].strip()
        if inline_header not in sections:
            sections[inline_header] = content

    return sections

def smart_chunk_split(text: str) -> list:
    blocks = [b.strip() for b in text.split("\n\n") if len(b.strip().split()) > 5]
    return blocks


def segment_resume_sections(text: str) -> dict:
    text = clean_resume_text(text)
    regex_sections = regex_segment(text)
    seen_chunks = set(regex_sections.keys())
    

    blocks = smart_chunk_split(text)
    remaining_blocks = [b for b in blocks if b not in seen_chunks]

    zsc_sections = classify_chunks(remaining_blocks, threshold=0.3)
    zsc_sections = {k: v for k, v in zsc_sections.items() if k not in seen_chunks}

    final = {**regex_sections, **zsc_sections}
    final = {k: v for k, v in final.items() if k != "misc" and v.strip()}
    return final



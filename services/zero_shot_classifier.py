from typing import List, Dict
from transformers import pipeline

# Load model once
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CANDIDATE_LABELS = [
    "personal information", "contact information",
    "education", "experience", "work experience", "professional experience",
    "skills", "technical skills",
    "certifications", "certification"
]


def classify_chunks(chunks: List[str], threshold=0.2) -> Dict[str, str]:
    labeled = {}

    for chunk in chunks:
        result = zero_shot(chunk, CANDIDATE_LABELS)
        label = result["labels"][0]
        score = result["scores"][0]

        print(f"\n[ZSC] Chunk: {chunk[:100]}...")
        print(f"[ZSC] Predicted: {label} ({score:.2f})")

        if score >= threshold:
            labeled.setdefault(label, "")
            labeled[label] += "\n\n" + chunk
        # else: silently skip low-confidence chunks

    return labeled
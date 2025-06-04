import pymupdf  
import re

def extract_clean_text_from_pdf(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    text_pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        lines = text.split('\n')
        if len(lines) > 2:
            lines = lines[1:-1]
        page_text = "\n".join(lines)
        text_pages.append(page_text)

    full_text = "\n".join(text_pages)
    for bullet in ["●", "•", "▪", "◦"]:
        full_text = full_text.replace(bullet, "")

    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    cleaned_lines = [line.strip() for line in full_text.split('\n')]
    cleaned_lines = [line for line in cleaned_lines if line]
    return "\n".join(cleaned_lines)

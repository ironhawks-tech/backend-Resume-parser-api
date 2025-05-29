import pymupdf  
import re

def extract_clean_text_from_pdf(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    text_pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()

        # Split page text into lines
        lines = text.split('\n')

        # Remove first and last line assuming headers/footers
        if len(lines) > 2:
            lines = lines[1:-1]

        # Join back lines after header n footer removal
        page_text = "\n".join(lines)
        text_pages.append(page_text)

    # Combine all pages
    full_text = "\n".join(text_pages)

    # Remove bullet points 
    for bullet in ["●", "•", "▪", "◦"]:
        full_text = full_text.replace(bullet, "")


    # Remove extra whitespace and blank lines (3+ newlines → 2 newlines)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)

    # Strip leading/trailing whitespace on each line
    cleaned_lines = [line.strip() for line in full_text.split('\n')]

    # Remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line]

    # Join lines with newline
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text
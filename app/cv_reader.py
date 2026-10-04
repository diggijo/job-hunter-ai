import re
import pymupdf


def clean_text_block(block_text):
    lines = [
        line.strip()
        for line in block_text.splitlines()
        if line.strip()
    ]

    text = " ".join(lines)

    text = re.sub(r"\s+", " ", text)

    return text


def extract_cv_text(pdf_path):
    doc = pymupdf.open(pdf_path)

    text_blocks = []

    for page in doc:
        blocks = page.get_text("blocks")

        for block in blocks:
            block_text = block[4]
            cleaned_text = clean_text_block(block_text)

            if cleaned_text:
                text_blocks.append(cleaned_text)

    doc.close()

    return "\n\n".join(text_blocks)
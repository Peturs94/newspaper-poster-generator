import fitz
import json

# Tuned for old Icelandic newspaper OCR
TITLE_FONT_MIN = 12
SUBTITLE_FONT_MIN = 11


def extract_lines(pdf_path):
    """Extract text lines with font size, using PyMuPDF's native block/line structure
    to preserve column boundaries."""
    doc = fitz.open(pdf_path)
    all_lines = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        # Sort blocks top-to-bottom, left-to-right so reading order is sensible
        blocks = sorted(blocks, key=lambda b: (round(b["bbox"][1] / 20), b["bbox"][0]))
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = " ".join(s["text"].strip() for s in spans if s["text"].strip())
                if not text:
                    continue
                max_size = max(s["size"] for s in spans if s["text"].strip())
                all_lines.append({"text": text, "size": max_size})

    return all_lines


def detect_articles(lines):
    """Article detection: Title -> optional subtitle -> body text."""
    articles = []
    current_title = None
    current_sub = None
    body_lines = []

    for line in lines:
        text = line["text"]
        size = line["size"]

        # TITLE
        if size >= TITLE_FONT_MIN and len(text) < 80:
            if current_title:
                articles.append({
                    "title": current_title,
                    "subtitle": current_sub or "",
                    "body": "\n".join(body_lines).strip()
                })
                body_lines = []

            current_title = text
            current_sub = None
            continue

        # SUBTITLE
        if size >= SUBTITLE_FONT_MIN and len(text) < 100:
            if current_title and current_sub is None:
                current_sub = text
                continue

        # BODY
        if current_title:
            body_lines.append(text)

    # Save last article
    if current_title:
        articles.append({
            "title": current_title,
            "subtitle": current_sub or "",
            "body": "\n".join(body_lines).strip()
        })

    return articles


def process_pdf(pdf_path, out_path="output.json"):
    lines = extract_lines(pdf_path)
    articles = detect_articles(lines)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} structured articles to {out_path}")


if __name__ == "__main__":
    import sys
    process_pdf(sys.argv[1])

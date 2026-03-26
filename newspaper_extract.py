import fitz
import json

# Tuned for old Icelandic newspaper OCR
TITLE_FONT_MIN = 16
SUBTITLE_FONT_MIN = 13


def extract_blocks(pdf_path):
    """Extract all text spans with font and position."""
    doc = fitz.open(pdf_path)
    all_spans = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    all_spans.append({
                        "text": span["text"].strip(),
                        "size": span["size"],
                        "font": span["font"],
                        "bbox": span["bbox"]
                    })
    return all_spans


def group_lines(spans, y_threshold=8):
    """Group spans into lines based on Y coordinate."""
    spans = sorted(spans, key=lambda s: s["bbox"][1])

    lines = []
    current = []
    last_y = None

    for s in spans:
        y = s["bbox"][1]

        if last_y is None or abs(y - last_y) <= y_threshold:
            current.append(s)
        else:
            lines.append(current)
            current = [s]

        last_y = y

    if current:
        lines.append(current)

    # Combine spans per line
    combined_lines = []
    for line in lines:
        text = " ".join(s["text"] for s in line).strip()
        max_size = max(s["size"] for s in line)
        avg_y = sum(s["bbox"][1] for s in line) / len(line)
        combined_lines.append({"text": text, "size": max_size, "y": avg_y})

    return combined_lines


def detect_articles(lines):
    """Article detection: Title → optional subtitle → body text."""
    articles = []
    current_title = None
    current_sub = None
    body_lines = []

    for line in lines:
        text = line["text"]
        size = line["size"]

        # TITLE
        if size >= TITLE_FONT_MIN and len(text) < 80:
            # Save previous article if exists
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
    spans = extract_blocks(pdf_path)
    lines = group_lines(spans)
    articles = detect_articles(lines)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} structured articles to {out_path}")


if __name__ == "__main__":
    import sys
    process_pdf(sys.argv[1])

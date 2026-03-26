import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import json

# -----------------------
# SETTINGS
# -----------------------
MIN_TITLE_FONT_HEIGHT = 18   # OCR bounding box height threshold
MAX_TITLE_LENGTH = 60        # short lines considered titles
CONFIDENCE_THRESHOLD = 60    # ignore garbage OCR
DEBUG = False


def looks_like_title(text):
    """Heuristic rules for title detection."""
    text = text.strip()

    # Ignore very short garbage lines
    if len(text) < 3:
        return False

    # Titles are usually short
    if len(text) > MAX_TITLE_LENGTH:
        return False

    # Titles often have Title Case or Capital Words
    if text == text.upper():
        return True
    if text.istitle():
        return True

    # Often no punctuation
    if not re.search(r'[.!?;:,()]', text):
        return True

    return False


def extract_ocr_data(image):
    """Extract bounding boxes + text using Tesseract TSV output."""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    lines = []

    for i in range(len(data["text"])):
        conf = int(data["conf"][i])
        if conf < CONFIDENCE_THRESHOLD:
            continue

        text = data["text"][i].strip()
        if not text:
            continue

        line_data = {
            "text": text,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
        }
        lines.append(line_data)

    return lines


def group_into_lines(boxes, y_threshold=10):
    """Group OCR fragments into full text lines based on Y proximity."""
    if not boxes:
        return []

    boxes = sorted(boxes, key=lambda x: (x["top"], x["left"]))

    lines = []
    current_line = []
    last_y = boxes[0]["top"]

    for box in boxes:
        if abs(box["top"] - last_y) <= y_threshold:
            current_line.append(box)
        else:
            lines.append(current_line)
            current_line = [box]
            last_y = box["top"]

    if current_line:
        lines.append(current_line)

    # Combine text within each line
    combined = []
    for line in lines:
        text = " ".join([b["text"] for b in line])
        max_height = max(b["height"] for b in line)
        combined.append({"text": text, "height": max_height})

    return combined


def extract_articles(lines):
    """Detect titles and group following text as article body."""
    articles = []
    current_title = None
    current_body = []

    for line in lines:
        text = line["text"]
        height = line["height"]

        is_title = looks_like_title(text) or height >= MIN_TITLE_FONT_HEIGHT

        if is_title:
            # Save existing article
            if current_title:
                articles.append({
                    "title": current_title,
                    "body": " ".join(current_body).strip()
                })
                current_body = []

            current_title = text

        else:
            if current_title:
                current_body.append(text)

    # Save last article
    if current_title:
        articles.append({
            "title": current_title,
            "body": " ".join(current_body).strip()
        })

    return articles


def process_pdf(pdf_path):
    print("Converting PDF pages to images...")
    pages = convert_from_path(pdf_path, dpi=300)

    all_lines = []

    for i, page in enumerate(pages):
        print(f"OCR on page {i+1}...")
        boxes = extract_ocr_data(page)
        lines = group_into_lines(boxes)
        all_lines.extend(lines)

    print("Detecting articles...")
    articles = extract_articles(all_lines)

    return articles


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract structured articles from newspaper PDF")
    parser.add_argument("pdf", help="Input PDF file")
    parser.add_argument("-o", "--output", default="articles.json", help="Output JSON file")
    args = parser.parse_args()

    articles = process_pdf(args.pdf)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Saved structured articles to {args.output}")

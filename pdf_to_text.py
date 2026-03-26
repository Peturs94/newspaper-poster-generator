import sys
import pathlib
from pdfminer.high_level import extract_text

def pdf_to_text(input_path, output_path):
    # Extract text using pdfminer
    text = extract_text(input_path)

    # Clean up excessive whitespace
    clean_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    # Write to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print(f"Saved clean text to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_text.py input.pdf output.txt")
        sys.exit(1)

    input_pdf = pathlib.Path(sys.argv[1])
    output_txt = pathlib.Path(sys.argv[2])

    if not input_pdf.exists():
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)

    pdf_to_text(input_pdf, output_txt)

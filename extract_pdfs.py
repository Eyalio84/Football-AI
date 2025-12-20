"""
PDF Text Extractor for Soccer-AI

Extracts text from Wikipedia PDFs in team folders
and saves as markdown for the parser to ingest.
"""

import os
from pathlib import Path
from pypdf import PdfReader


def extract_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(str(pdf_path))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"  Error extracting {pdf_path.name}: {e}")
        return ""


def process_folder(folder_path: Path, club_name: str):
    """Process all PDFs in a folder and create combined markdown."""
    pdfs = list(folder_path.glob("*.PDF")) + list(folder_path.glob("*.pdf"))

    if not pdfs:
        print(f"  No PDFs found in {folder_path.name}")
        return

    print(f"\n=== Processing {club_name} ({len(pdfs)} PDFs) ===")

    combined_text = f"# {club_name}\n\n"

    for pdf in pdfs:
        print(f"  Extracting: {pdf.name}")
        text = extract_pdf(pdf)
        if text:
            # Add section header based on PDF name
            section_name = pdf.stem.replace(" - Wikipedia", "").replace("_", " ")
            combined_text += f"## {section_name}\n\n{text}\n\n---\n\n"

    # Save to markdown file
    output_path = folder_path / f"{club_name.lower().replace(' ', '_')}.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(combined_text)

    print(f"  Saved: {output_path.name} ({len(combined_text)} chars)")
    return output_path


def main():
    parser_path = Path("/storage/emulated/0/Download/Manchester/parser")

    # Team folders and their proper names
    team_folders = [
        ("Liverpool", "Liverpool"),
        ("Manchster city", "Manchester City"),
        ("arsenal", "Arsenal"),
        ("aston villa", "Aston Villa"),
        ("chelsea", "Chelsea"),
        ("newcastle", "Newcastle United"),
        ("tottenham", "Tottenham Hotspur"),
        ("west ham", "West Ham United"),
        ("leeds", "Leeds United"),
        ("leicester", "Leicester City"),
        ("sunderland", "Sunderland"),
    ]

    extracted_files = []

    for folder_name, club_name in team_folders:
        folder = parser_path / folder_name
        if folder.exists():
            result = process_folder(folder, club_name)
            if result:
                extracted_files.append(result)

    # Also extract the Leeds PDF from root
    leeds_pdf = parser_path / "Leeds United F.C.PDF"
    if leeds_pdf.exists():
        print(f"\n=== Processing Leeds PDF from root ===")
        text = extract_pdf(leeds_pdf)
        if text:
            output = parser_path / "leeds" / "leeds_united.md"
            output.parent.mkdir(exist_ok=True)
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f"# Leeds United\n\n{text}")
            print(f"  Saved: {output}")
            extracted_files.append(output)

    print(f"\n=== Extraction Complete ===")
    print(f"Created {len(extracted_files)} markdown files")
    print("\nNow run: python3 parse_team_content.py")


if __name__ == "__main__":
    main()

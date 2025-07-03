import fitz  # PyMuPDF
import re
import os
import json

def extract_reference_titles(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(
        page.get_text("text", clip=fitz.Rect(page.rect.x0,
                                            page.rect.y0 + 0.03 * page.rect.height,
                                            page.rect.x1,
                                            page.rect.y1 - 0.03 * page.rect.height))
        for page in doc
    )

    # Step 1: Find References section
    ref_start = re.search(r'\bReferences\b', text, re.IGNORECASE)
    disclaimer_start = re.search(r'\bDisclaimer: This generalized information is\b', text)
    if not ref_start:
        raise ValueError("Could not find 'References' section.")
    if not disclaimer_start:
        raise ValueError("Could not find 'Disclaimer' section.")
    ref_text = text[ref_start.end():disclaimer_start.start()].strip()


    # Step 2: Split into entries (often starts with numbers)
    raw_entries = re.split(r'\n\d{1,3}\.\s+', ref_text)
    titles = []

    for entry in raw_entries:
        entry = entry.replace('\n', ' ').strip()
        # Simple heuristic: look for sentence between first period and journal/year
        match = re.search(r'\. (.*?)\. [A-Z].+?\d{4}', entry)
        if match:
            title = match.group(1).strip()
            titles.append(title)

    return titles


dir_of_chapters = "/home/yishan-zhong/MIMIC-III-Agents/UpToDate-MIMIC3"

chapter_dirs = [os.path.join(dir_of_chapters, d) for d in os.listdir(dir_of_chapters) if os.path.isdir(os.path.join(dir_of_chapters, d))]

for chapter_dir in chapter_dirs:

    within_chapter_dir = chapter_dir
    refs_of_chapter = []
    condition_dirs = [os.path.join(within_chapter_dir, d) for d in os.listdir(within_chapter_dir) if os.path.isdir(os.path.join(within_chapter_dir, d))]
    for condition_dir in condition_dirs:
        pdf_files_path = [os.path.join(condition_dir, f) for f in os.listdir(condition_dir) if f.endswith('.pdf')]

        for pdf_file in pdf_files_path:
            try:
                titles = extract_reference_titles(pdf_file)

                # print("=" * 20)
                # for i, title in enumerate(titles, 1):
                #     print(f"{i}. {title}")
                for i, title in enumerate(titles, 1):
                    refs_of_chapter.append({
                        "condition": os.path.basename(condition_dir),
                        "title": title,
                        "pdf_file": os.path.basename(pdf_file).replace(" - UpToDate", ""),
                        "index": i,
                    })
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                continue

    print(f"Extracted {len(refs_of_chapter)} references from {len(pdf_files_path)} PDFs in chapter {within_chapter_dir}")
    with open(os.path.join(within_chapter_dir, "references.json"), "w") as f:
        json.dump(refs_of_chapter, f, indent=4)

#!/usr/bin/env python3
"""
PDF Text Extractor - Bypasses Claude API limitations
Extracts all text from construction document PDFs for analysis
"""

import sys
import pdfplumber
from pathlib import Path

def extract_pdf_info(pdf_path):
    """Extract comprehensive info from PDF"""

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return None

    print(f"\n{'='*80}")
    print(f"Extracting: {pdf_path.name}")
    print(f"Size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"{'='*80}\n")

    results = {
        'filename': pdf_path.name,
        'pages': [],
        'total_pages': 0,
        'sheet_names': [],
        'metadata': {}
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            results['total_pages'] = len(pdf.pages)
            results['metadata'] = pdf.metadata or {}

            print(f"Total Pages: {len(pdf.pages)}")
            print(f"Metadata: {pdf.metadata}\n")

            for i, page in enumerate(pdf.pages, 1):
                print(f"Processing page {i}/{len(pdf.pages)}...", end='\r')

                text = page.extract_text() or ""

                # Extract first line as potential sheet name
                first_line = text.split('\n')[0] if text else ""

                page_info = {
                    'page_num': i,
                    'text': text,
                    'first_line': first_line,
                    'char_count': len(text)
                }

                results['pages'].append(page_info)

                # Collect potential sheet names (first line of each page)
                if first_line:
                    results['sheet_names'].append(f"Page {i}: {first_line[:100]}")

            print(f"\n\nExtraction complete! {len(pdf.pages)} pages processed.")

    except Exception as e:
        print(f"ERROR: {e}")
        return None

    return results

def save_results(results, output_path):
    """Save extracted text to file"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"PDF Analysis: {results['filename']}\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"Total Pages: {results['total_pages']}\n")
        f.write(f"Metadata: {results['metadata']}\n\n")

        f.write(f"Sheet Names (First Lines):\n")
        f.write(f"{'-'*80}\n")
        for sheet_name in results['sheet_names']:
            f.write(f"{sheet_name}\n")

        f.write(f"\n\n{'='*80}\n")
        f.write(f"FULL TEXT EXTRACTION\n")
        f.write(f"{'='*80}\n\n")

        for page in results['pages']:
            f.write(f"\n{'='*80}\n")
            f.write(f"PAGE {page['page_num']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(page['text'])
            f.write(f"\n\n")

    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf_text.py <pdf_file> [output_file]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"{Path(pdf_file).stem}_extracted.txt"

    results = extract_pdf_info(pdf_file)

    if results:
        save_results(results, output_file)
        print(f"\n✓ SUCCESS: PDF processed without any API limitations!")
        print(f"✓ You can now read: {output_file}")
    else:
        print("\n✗ FAILED: Could not extract PDF")
        sys.exit(1)

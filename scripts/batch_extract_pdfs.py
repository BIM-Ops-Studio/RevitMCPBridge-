#!/usr/bin/env python3
"""
Batch PDF Extractor - Process all construction document PDFs for learning
"""

import sys
import os
from pathlib import Path
import pdfplumber
import json

def extract_pdf_summary(pdf_path):
    """Extract summary information from PDF"""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            metadata = pdf.metadata or {}
            total_pages = len(pdf.pages)

            # Extract first lines from first 10 pages to get sheet names
            sheet_names = []
            for i, page in enumerate(pdf.pages[:min(10, total_pages)]):
                text = page.extract_text() or ""
                first_line = text.split('\n')[0] if text else ""
                if first_line and len(first_line) < 100:
                    sheet_names.append(f"Page {i+1}: {first_line}")

            return {
                'filename': pdf_path.name,
                'total_pages': total_pages,
                'size_mb': pdf_path.stat().st_size / (1024*1024),
                'metadata': metadata,
                'sheet_names_sample': sheet_names,
                'success': True
            }
    except Exception as e:
        return {
            'filename': pdf_path.name,
            'error': str(e),
            'success': False
        }

def batch_extract_directory(directory_path, output_dir):
    """Extract all PDFs in directory and subdirectories"""

    directory = Path(directory_path)
    output = Path(output_dir)
    output.mkdir(exist_ok=True)

    # Find all PDFs
    pdf_files = list(directory.rglob("*.pdf"))

    print(f"\nFound {len(pdf_files)} PDF files to process")
    print(f"{'='*80}\n")

    results = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        print(f"  Location: {pdf_path.parent}")
        print(f"  Size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")

        summary = extract_pdf_summary(pdf_path)
        summary['relative_path'] = str(pdf_path.relative_to(directory))
        results.append(summary)

        if summary['success']:
            print(f"  ✓ Success: {summary['total_pages']} pages")
        else:
            print(f"  ✗ Error: {summary['error']}")

        print()

    # Save summary report
    report_path = output / "pdf_extraction_summary.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"{'='*80}")
    print(f"Extraction complete!")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Summary saved to: {report_path}")

    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 batch_extract_pdfs.py <pdf_directory> <output_directory>")
        sys.exit(1)

    pdf_dir = sys.argv[1]
    output_dir = sys.argv[2]

    results = batch_extract_directory(pdf_dir, output_dir)

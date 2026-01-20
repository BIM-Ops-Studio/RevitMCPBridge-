"""
Convert PDF construction documents to images for analysis
"""
import os
import sys

def convert_pdf_with_pymupdf(pdf_path, output_dir):
    """Use PyMuPDF (fitz) to convert PDF to images"""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        print(f"PDF has {len(doc)} pages")

        os.makedirs(output_dir, exist_ok=True)

        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # High resolution for construction documents
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)

            output_path = os.path.join(output_dir, f"page_{page_num + 1:03d}.png")
            pix.save(output_path)
            images.append(output_path)
            print(f"  Converted page {page_num + 1}: {output_path}")

        doc.close()
        return images

    except ImportError:
        print("PyMuPDF not available, trying pdf2image...")
        return None

def convert_pdf_with_pdf2image(pdf_path, output_dir):
    """Use pdf2image to convert PDF to images (requires poppler)"""
    try:
        from pdf2image import convert_from_path

        os.makedirs(output_dir, exist_ok=True)

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=200)
        print(f"PDF has {len(images)} pages")

        output_paths = []
        for i, image in enumerate(images):
            output_path = os.path.join(output_dir, f"page_{i + 1:03d}.png")
            image.save(output_path, 'PNG')
            output_paths.append(output_path)
            print(f"  Converted page {i + 1}: {output_path}")

        return output_paths

    except ImportError:
        print("pdf2image not available")
        return None
    except Exception as e:
        print(f"pdf2image error: {e}")
        return None

def main():
    pdf_path = r"D:\RevitMCPBridge2026\sample-pdf-sets\1700 West Sheffield Road.pdf"
    output_dir = r"D:\RevitMCPBridge2026\sample-pdf-sets\1700_West_Sheffield_Road_images"

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"Converting: {pdf_path}")
    print(f"Output to: {output_dir}")
    print("=" * 60)

    # Try PyMuPDF first (usually works without external dependencies)
    images = convert_pdf_with_pymupdf(pdf_path, output_dir)

    # Fall back to pdf2image if needed
    if images is None:
        images = convert_pdf_with_pdf2image(pdf_path, output_dir)

    if images:
        print("=" * 60)
        print(f"SUCCESS! Converted {len(images)} pages")
        print(f"Images saved to: {output_dir}")
        return images
    else:
        print("ERROR: Could not convert PDF")
        sys.exit(1)

if __name__ == "__main__":
    main()

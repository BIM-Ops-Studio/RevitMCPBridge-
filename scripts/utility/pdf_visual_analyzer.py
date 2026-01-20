#!/usr/bin/env python3
"""
PDF Floor Plan Visual Analyzer
Systematically scans a floor plan PDF to understand wall geometry

This tool:
1. Renders the PDF page to a high-resolution image
2. Divides it into a grid of quadrants
3. Analyzes each quadrant for wall segments
4. Builds a complete wall map with coordinates
5. Outputs a JSON spec ready for Revit
"""

import fitz  # PyMuPDF
import json
import os
from PIL import Image
import io

class FloorPlanAnalyzer:
    def __init__(self, pdf_path, page_number=0):
        self.pdf_path = pdf_path
        self.page_number = page_number
        self.doc = fitz.open(pdf_path)
        self.page = self.doc[page_number]

        # Get page dimensions
        self.page_rect = self.page.rect
        self.width = self.page_rect.width
        self.height = self.page_rect.height

        print(f"PDF Page: {self.width:.0f} x {self.height:.0f} points")

    def render_full_page(self, dpi=300, output_path=None):
        """Render the full page at high resolution"""
        zoom = dpi / 72  # 72 is default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = self.page.get_pixmap(matrix=mat)

        if output_path:
            pix.save(output_path)
            print(f"Saved full page to: {output_path}")

        return pix

    def render_quadrant(self, row, col, grid_size=3, dpi=300, output_dir=None):
        """
        Render a specific quadrant of the page

        Args:
            row: Row index (0 to grid_size-1, 0=top)
            col: Column index (0 to grid_size-1, 0=left)
            grid_size: Number of divisions (3 = 9 quadrants)
            dpi: Resolution
            output_dir: Directory to save quadrant images
        """
        # Calculate quadrant bounds
        quad_width = self.width / grid_size
        quad_height = self.height / grid_size

        x0 = col * quad_width
        y0 = row * quad_height
        x1 = x0 + quad_width
        y1 = y0 + quad_height

        clip = fitz.Rect(x0, y0, x1, y1)

        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = self.page.get_pixmap(matrix=mat, clip=clip)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"quadrant_{row}_{col}.png"
            filepath = os.path.join(output_dir, filename)
            pix.save(filepath)
            print(f"Saved quadrant ({row},{col}) to: {filepath}")

        return pix, clip

    def analyze_all_quadrants(self, grid_size=3, dpi=300, output_dir=None):
        """Render all quadrants and prepare for analysis"""
        quadrants = []

        for row in range(grid_size):
            for col in range(grid_size):
                pix, clip = self.render_quadrant(row, col, grid_size, dpi, output_dir)

                quadrant_info = {
                    "row": row,
                    "col": col,
                    "bounds": {
                        "x0": clip.x0,
                        "y0": clip.y0,
                        "x1": clip.x1,
                        "y1": clip.y1
                    },
                    "image_size": {
                        "width": pix.width,
                        "height": pix.height
                    }
                }
                quadrants.append(quadrant_info)

        return quadrants

    def extract_vector_paths(self):
        """Extract all vector drawing paths from the PDF"""
        drawings = self.page.get_drawings()

        paths = []
        for d in drawings:
            path_info = {
                "rect": [d["rect"].x0, d["rect"].y0, d["rect"].x1, d["rect"].y1],
                "items": []
            }

            for item in d["items"]:
                item_type = item[0]
                if item_type == "l":  # Line
                    path_info["items"].append({
                        "type": "line",
                        "start": [item[1].x, item[1].y],
                        "end": [item[2].x, item[2].y]
                    })
                elif item_type == "re":  # Rectangle
                    path_info["items"].append({
                        "type": "rect",
                        "rect": [item[1].x0, item[1].y0, item[1].x1, item[1].y1]
                    })
                elif item_type == "c":  # Curve
                    path_info["items"].append({
                        "type": "curve",
                        "points": [[p.x, p.y] for p in item[1:]]
                    })

            if path_info["items"]:
                paths.append(path_info)

        return paths

    def find_wall_candidates(self, min_length=10, max_thickness=20):
        """
        Find line segments that could be walls

        Walls are typically:
        - Long, straight lines
        - Horizontal or vertical (mostly)
        - Grouped in parallel pairs (representing wall thickness)
        """
        drawings = self.page.get_drawings()

        wall_candidates = []

        for d in drawings:
            for item in d["items"]:
                if item[0] == "l":  # Line segment
                    start = item[1]
                    end = item[2]

                    # Calculate length
                    dx = end.x - start.x
                    dy = end.y - start.y
                    length = (dx*dx + dy*dy) ** 0.5

                    if length >= min_length:
                        # Determine orientation
                        if abs(dx) < 1:  # Vertical
                            orientation = "vertical"
                        elif abs(dy) < 1:  # Horizontal
                            orientation = "horizontal"
                        else:
                            orientation = "angled"

                        wall_candidates.append({
                            "start": {"x": start.x, "y": start.y},
                            "end": {"x": end.x, "y": end.y},
                            "length": length,
                            "orientation": orientation,
                            "stroke_width": d.get("width", 1)
                        })

        return wall_candidates

    def extract_text_labels(self):
        """Extract all text from the page with positions"""
        blocks = self.page.get_text("dict")["blocks"]

        labels = []
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        labels.append({
                            "text": span["text"],
                            "bbox": list(span["bbox"]),
                            "font_size": span["size"]
                        })

        return labels

    def find_room_labels(self):
        """Find room name and number labels"""
        labels = self.extract_text_labels()

        room_keywords = [
            "GARAGE", "KITCHEN", "LIVING", "DINING", "BEDROOM", "BATH",
            "UTILITY", "CLOSET", "PANTRY", "PORCH", "LANAI", "FOYER",
            "HALLWAY", "STUDY", "OFFICE", "LAUNDRY"
        ]

        rooms = []
        for label in labels:
            text_upper = label["text"].upper()

            # Check for room keywords
            for keyword in room_keywords:
                if keyword in text_upper:
                    rooms.append(label)
                    break

            # Check for room numbers (3 digit pattern)
            if label["text"].strip().isdigit() and len(label["text"].strip()) == 3:
                rooms.append(label)

            # Check for SF (square footage)
            if "SF" in text_upper:
                rooms.append(label)

        return rooms

    def find_dimensions(self):
        """Find dimension strings like 12'-1" or 15'-0" """
        labels = self.extract_text_labels()

        import re
        dim_pattern = r"\d+['\-]\s*\d*[\"\']?"

        dimensions = []
        for label in labels:
            if re.search(dim_pattern, label["text"]):
                dimensions.append(label)

        return dimensions

    def build_analysis_report(self, output_dir=None):
        """Build a complete analysis report"""

        print("\n" + "="*60)
        print("FLOOR PLAN ANALYSIS REPORT")
        print("="*60)

        # 1. Basic info
        print(f"\nPDF: {self.pdf_path}")
        print(f"Page: {self.page_number + 1}")
        print(f"Dimensions: {self.width:.0f} x {self.height:.0f} points")

        # 2. Extract vectors
        print("\n--- VECTOR PATHS ---")
        paths = self.extract_vector_paths()
        print(f"Total drawing paths: {len(paths)}")

        # 3. Find wall candidates
        print("\n--- WALL CANDIDATES ---")
        walls = self.find_wall_candidates()
        print(f"Potential wall segments: {len(walls)}")

        horizontal = [w for w in walls if w["orientation"] == "horizontal"]
        vertical = [w for w in walls if w["orientation"] == "vertical"]
        angled = [w for w in walls if w["orientation"] == "angled"]

        print(f"  Horizontal: {len(horizontal)}")
        print(f"  Vertical: {len(vertical)}")
        print(f"  Angled: {len(angled)}")

        # 4. Find room labels
        print("\n--- ROOM LABELS ---")
        rooms = self.find_room_labels()
        print(f"Room labels found: {len(rooms)}")
        for room in rooms[:20]:  # First 20
            print(f"  '{room['text']}' at ({room['bbox'][0]:.0f}, {room['bbox'][1]:.0f})")

        # 5. Find dimensions
        print("\n--- DIMENSIONS ---")
        dims = self.find_dimensions()
        print(f"Dimension labels found: {len(dims)}")
        for dim in dims[:20]:  # First 20
            print(f"  '{dim['text']}' at ({dim['bbox'][0]:.0f}, {dim['bbox'][1]:.0f})")

        # 6. Render quadrants
        if output_dir:
            print(f"\n--- RENDERING QUADRANTS ---")
            os.makedirs(output_dir, exist_ok=True)

            # Full page
            self.render_full_page(dpi=200, output_path=os.path.join(output_dir, "full_page.png"))

            # 3x3 grid
            self.analyze_all_quadrants(grid_size=3, dpi=200, output_dir=output_dir)

        # Build report
        report = {
            "pdf": self.pdf_path,
            "page": self.page_number,
            "page_size": {"width": self.width, "height": self.height},
            "wall_candidates": walls,
            "room_labels": rooms,
            "dimensions": dims,
            "total_paths": len(paths)
        }

        if output_dir:
            report_path = os.path.join(output_dir, "analysis_report.json")
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {report_path}")

        return report

    def close(self):
        self.doc.close()


def main():
    # Analyze the RBCDC floor plan
    pdf_path = "/mnt/d/RevitMCPBridge2026/sample-pdf-sets/Florida-Sample-Projects/RBCDC-1713-2Story-Prototype/RBCDC 1713 2 Story Prototype Home.pdf"

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        # Try alternate location
        alt_paths = [
            "/mnt/d/001 - PROJECTS/01 - CLIENT PROJECTS/RBCDC/RBCDC 1713 2 Story Prototype Home.pdf",
            "/mnt/d/RevitMCPBridge2026/RBCDC 1713 2 Story Prototype Home.pdf"
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                pdf_path = alt
                print(f"Found at: {pdf_path}")
                break

    output_dir = "/mnt/d/RevitMCPBridge2026/floor_plan_analysis"

    # Find the A-100 page (1st & 2nd Floor Plans)
    doc = fitz.open(pdf_path)
    target_page = None

    for i, page in enumerate(doc):
        text = page.get_text()
        if "A-100" in text or "1ST FLOOR" in text.upper():
            target_page = i
            print(f"Found floor plan on page {i+1}")
            break

    doc.close()

    if target_page is None:
        target_page = 4  # Default to page 5 (0-indexed = 4)
        print(f"Using default page {target_page + 1}")

    # Run analysis
    analyzer = FloorPlanAnalyzer(pdf_path, target_page)
    report = analyzer.build_analysis_report(output_dir)
    analyzer.close()

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\nQuadrant images saved to: {output_dir}")
    print("Review each quadrant image to understand the floor plan layout")
    print("\nNext steps:")
    print("1. Look at each quadrant image")
    print("2. Identify walls in each section")
    print("3. Map coordinates from PDF space to Revit space")


if __name__ == "__main__":
    main()

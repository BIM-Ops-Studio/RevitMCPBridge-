#!/usr/bin/env python3
"""
Floor Plan Wall Extractor
Uses OpenCV for line detection and OCR for dimension reading

This tool:
1. Loads a floor plan image
2. Detects wall lines using edge detection and Hough transform
3. Reads dimension text using OCR
4. Correlates wall positions to a coordinate system
5. Outputs wall definitions ready for Revit
"""

import cv2
import numpy as np
from PIL import Image
import json
import os
import re

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract not installed. OCR features disabled.")
    print("Install with: pip install pytesseract")


class WallExtractor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.original = cv2.imread(image_path)
        if self.original is None:
            raise ValueError(f"Could not load image: {image_path}")

        self.height, self.width = self.original.shape[:2]
        self.gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)

        # Store detected elements
        self.lines = []
        self.wall_segments = []
        self.dimensions = []
        self.grid_lines = {"horizontal": [], "vertical": []}

        print(f"Loaded image: {self.width} x {self.height} pixels")

    def detect_lines(self, threshold1=50, threshold2=150, min_line_length=50, max_line_gap=10):
        """
        Detect lines using Canny edge detection and Hough Line Transform
        """
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, threshold1, threshold2)

        # Probabilistic Hough Line Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )

        if lines is not None:
            self.lines = lines.reshape(-1, 4)  # Each line: [x1, y1, x2, y2]
            print(f"Detected {len(self.lines)} line segments")
        else:
            self.lines = []
            print("No lines detected")

        return self.lines

    def classify_lines(self, angle_tolerance=5):
        """
        Classify lines as horizontal, vertical, or angled
        """
        horizontal = []
        vertical = []
        angled = []

        for line in self.lines:
            x1, y1, x2, y2 = line
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx*dx + dy*dy)

            if length < 10:  # Skip very short lines
                continue

            # Calculate angle from horizontal
            angle = np.degrees(np.arctan2(abs(dy), abs(dx)))

            if angle < angle_tolerance:
                horizontal.append({
                    "x1": int(x1), "y1": int(y1),
                    "x2": int(x2), "y2": int(y2),
                    "length": float(length),
                    "angle": float(angle)
                })
            elif angle > (90 - angle_tolerance):
                vertical.append({
                    "x1": int(x1), "y1": int(y1),
                    "x2": int(x2), "y2": int(y2),
                    "length": float(length),
                    "angle": float(angle)
                })
            else:
                angled.append({
                    "x1": int(x1), "y1": int(y1),
                    "x2": int(x2), "y2": int(y2),
                    "length": float(length),
                    "angle": float(angle)
                })

        print(f"Classified lines: {len(horizontal)} horizontal, {len(vertical)} vertical, {len(angled)} angled")

        return {"horizontal": horizontal, "vertical": vertical, "angled": angled}

    def detect_thick_lines(self, min_thickness=3):
        """
        Detect thick lines (walls) by analyzing line width
        Uses morphological operations
        """
        # Threshold to get binary image
        _, binary = cv2.threshold(self.gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        thick_segments = []
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate aspect ratio to identify line-like shapes
            if w > 0 and h > 0:
                aspect = max(w, h) / min(w, h)

                # Line-like shapes have high aspect ratio
                if aspect > 5:
                    # Check if it's thick enough
                    thickness = min(w, h)
                    if thickness >= min_thickness:
                        # Determine orientation
                        if w > h:
                            orientation = "horizontal"
                        else:
                            orientation = "vertical"

                        thick_segments.append({
                            "x": int(x),
                            "y": int(y),
                            "width": int(w),
                            "height": int(h),
                            "thickness": int(thickness),
                            "orientation": orientation,
                            "length": int(max(w, h))
                        })

        print(f"Detected {len(thick_segments)} thick line segments (potential walls)")
        return thick_segments

    def extract_text_regions(self):
        """
        Use OCR to extract text from the image
        """
        if not HAS_OCR:
            print("OCR not available")
            return []

        # Get OCR data with bounding boxes
        try:
            data = pytesseract.image_to_data(self.original, output_type=pytesseract.Output.DICT)
        except Exception as e:
            print(f"OCR error: {e}")
            return []

        text_regions = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = int(data['conf'][i])

                if conf > 30:  # Only keep confident detections
                    text_regions.append({
                        "text": text,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "confidence": conf
                    })

        print(f"Extracted {len(text_regions)} text regions via OCR")
        return text_regions

    def find_dimensions(self, text_regions=None):
        """
        Find dimension strings in text (like 12'-1", 8'-0", etc.)
        """
        if text_regions is None:
            text_regions = self.extract_text_regions()

        # Pattern for architectural dimensions
        # Matches: 12'-1", 8'-0", 15' - 4", etc.
        dim_pattern = r"(\d+)['\s]*[-]?\s*(\d*)[\"\']?"

        dimensions = []
        for region in text_regions:
            text = region["text"]
            matches = re.findall(dim_pattern, text)

            for match in matches:
                feet = int(match[0])
                inches = int(match[1]) if match[1] else 0
                total_feet = feet + inches / 12.0

                dimensions.append({
                    "text": text,
                    "feet": feet,
                    "inches": inches,
                    "total_feet": total_feet,
                    "x": region["x"],
                    "y": region["y"],
                    "width": region["width"],
                    "height": region["height"]
                })

        self.dimensions = dimensions
        print(f"Found {len(dimensions)} dimension strings")
        return dimensions

    def find_room_labels(self, text_regions=None):
        """
        Find room name labels
        """
        if text_regions is None:
            text_regions = self.extract_text_regions()

        room_keywords = [
            "GARAGE", "KITCHEN", "LIVING", "DINING", "BEDROOM", "BATH",
            "UTILITY", "CLOSET", "PANTRY", "PORCH", "LANAI", "FOYER",
            "HALLWAY", "STUDY", "OFFICE", "LAUNDRY", "ENTRY"
        ]

        rooms = []
        for region in text_regions:
            text_upper = region["text"].upper()
            for keyword in room_keywords:
                if keyword in text_upper:
                    rooms.append({
                        "name": region["text"],
                        "keyword": keyword,
                        "x": region["x"],
                        "y": region["y"],
                        "center_x": region["x"] + region["width"] // 2,
                        "center_y": region["y"] + region["height"] // 2
                    })
                    break

        print(f"Found {len(rooms)} room labels")
        return rooms

    def detect_grid_bubbles(self):
        """
        Detect grid bubbles (circles with letters/numbers)
        Using Hough Circle Transform
        """
        # Blur and detect circles
        blurred = cv2.medianBlur(self.gray, 5)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=15,
            maxRadius=40
        )

        grid_bubbles = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                x, y, r = circle
                grid_bubbles.append({
                    "x": int(x),
                    "y": int(y),
                    "radius": int(r)
                })

        print(f"Detected {len(grid_bubbles)} potential grid bubbles")
        return grid_bubbles

    def visualize_detections(self, output_path, show_lines=True, show_thick=True, show_text=False):
        """
        Create a visualization of detected elements
        """
        vis = self.original.copy()

        if show_lines and len(self.lines) > 0:
            for line in self.lines:
                x1, y1, x2, y2 = line
                cv2.line(vis, (x1, y1), (x2, y2), (0, 255, 0), 1)

        if show_thick:
            thick = self.detect_thick_lines()
            for seg in thick:
                x, y, w, h = seg["x"], seg["y"], seg["width"], seg["height"]
                cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)

        if show_text and self.dimensions:
            for dim in self.dimensions:
                x, y = dim["x"], dim["y"]
                cv2.circle(vis, (x, y), 5, (255, 0, 0), -1)
                cv2.putText(vis, f"{dim['total_feet']:.1f}'", (x, y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        cv2.imwrite(output_path, vis)
        print(f"Saved visualization to: {output_path}")

    def analyze(self, output_dir=None):
        """
        Run full analysis pipeline
        """
        print("\n" + "="*60)
        print("FLOOR PLAN ANALYSIS")
        print("="*60)

        # Detect lines
        self.detect_lines()

        # Classify lines
        classified = self.classify_lines()

        # Detect thick lines (walls)
        thick_lines = self.detect_thick_lines()

        # Extract text
        text_regions = []
        dimensions = []
        rooms = []

        if HAS_OCR:
            text_regions = self.extract_text_regions()
            dimensions = self.find_dimensions(text_regions)
            rooms = self.find_room_labels(text_regions)

        # Detect grid bubbles
        grid_bubbles = self.detect_grid_bubbles()

        # Compile results
        results = {
            "image": {
                "path": self.image_path,
                "width": self.width,
                "height": self.height
            },
            "lines": {
                "total": len(self.lines),
                "horizontal": len(classified["horizontal"]),
                "vertical": len(classified["vertical"]),
                "angled": len(classified["angled"])
            },
            "thick_segments": thick_lines,
            "dimensions": dimensions,
            "rooms": rooms,
            "grid_bubbles": grid_bubbles
        }

        # Save results
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

            # Save JSON report
            report_path = os.path.join(output_dir, "analysis_report.json")
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nSaved analysis report: {report_path}")

            # Save visualization
            vis_path = os.path.join(output_dir, "detected_walls.png")
            self.visualize_detections(vis_path)

        return results


def analyze_floor_plan(image_path, output_dir=None):
    """
    Main entry point for floor plan analysis
    """
    extractor = WallExtractor(image_path)
    results = extractor.analyze(output_dir)
    return results


if __name__ == "__main__":
    # Analyze the 1st floor plan
    image_path = "/mnt/d/RevitMCPBridge2026/floor_plan_quadrants/1st_floor_only.png"
    output_dir = "/mnt/d/RevitMCPBridge2026/wall_extraction_results"

    if os.path.exists(image_path):
        results = analyze_floor_plan(image_path, output_dir)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total line segments: {results['lines']['total']}")
        print(f"  Horizontal: {results['lines']['horizontal']}")
        print(f"  Vertical: {results['lines']['vertical']}")
        print(f"Thick segments (walls): {len(results['thick_segments'])}")
        print(f"Dimensions found: {len(results['dimensions'])}")
        print(f"Room labels: {len(results['rooms'])}")
        print(f"Grid bubbles: {len(results['grid_bubbles'])}")

        if results['dimensions']:
            print("\nDimensions detected:")
            for dim in results['dimensions'][:10]:
                print(f"  {dim['text']} = {dim['total_feet']:.2f} feet")

        if results['rooms']:
            print("\nRooms detected:")
            for room in results['rooms']:
                print(f"  {room['name']} at ({room['center_x']}, {room['center_y']})")
    else:
        print(f"Image not found: {image_path}")
        print("Run split_floor_plan.py first to create quadrant images")

"""
Automatic Wall Detection from PDF Floor Plans

This tool automatically detects walls from architectural floor plan PDFs by:
1. Extracting vector line data from PDF
2. Filtering lines by thickness, length, and orientation
3. Grouping parallel lines into wall segments
4. Connecting walls at intersections
5. Generating Revit wall commands

Usage:
    python auto_wall_detect.py <pdf_path> [page_number]
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
    import fitz

try:
    import numpy as np
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
    import numpy as np


class AutoWallDetector:
    def __init__(self, pdf_path, page_num=0):
        self.pdf_path = pdf_path
        self.page_num = page_num

        # Detection parameters (tunable)
        self.min_wall_length = 10  # Minimum wall length in PDF points
        self.wall_thickness_range = (0.5, 10)  # Line width range for walls
        self.angle_tolerance = 5  # Degrees tolerance for H/V lines
        self.snap_distance = 5  # Distance to snap endpoints together

        # Results
        self.all_lines = []
        self.wall_lines = []
        self.wall_segments = []
        self.scale_factor = None

        # PDF info
        self.page_width = 0
        self.page_height = 0

    def load_pdf(self):
        """Load PDF and extract page info"""
        self.doc = fitz.open(self.pdf_path)
        self.page = self.doc[self.page_num]
        self.page_width = self.page.rect.width
        self.page_height = self.page.rect.height
        print(f"Loaded page {self.page_num}: {self.page_width:.1f} x {self.page_height:.1f} points")

    def extract_lines(self):
        """Extract all line paths from PDF"""
        print("Extracting lines from PDF...")

        # Get all drawings on the page
        paths = self.page.get_drawings()

        line_count = 0
        rect_count = 0

        for path in paths:
            # Each path has items like ('l', p1, p2) for lines, ('re', rect) for rectangles
            color = path.get('color', (0, 0, 0))
            width = path.get('width', 1)
            fill = path.get('fill')

            for item in path['items']:
                if item[0] == 'l':  # Line
                    p1, p2 = item[1], item[2]
                    line = {
                        'start': (p1.x, p1.y),
                        'end': (p2.x, p2.y),
                        'width': width,
                        'color': color,
                        'length': math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
                    }
                    # Calculate angle
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    line['angle'] = math.degrees(math.atan2(dy, dx)) % 180
                    self.all_lines.append(line)
                    line_count += 1

                elif item[0] == 're':  # Rectangle - convert to 4 lines
                    rect = item[1]
                    corners = [
                        (rect.x0, rect.y0),
                        (rect.x1, rect.y0),
                        (rect.x1, rect.y1),
                        (rect.x0, rect.y1)
                    ]
                    for i in range(4):
                        p1 = corners[i]
                        p2 = corners[(i + 1) % 4]
                        line = {
                            'start': p1,
                            'end': p2,
                            'width': width,
                            'color': color,
                            'length': math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2),
                            'from_rect': True
                        }
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        line['angle'] = math.degrees(math.atan2(dy, dx)) % 180
                        self.all_lines.append(line)
                    rect_count += 1

        print(f"  Found {line_count} lines and {rect_count} rectangles ({len(self.all_lines)} total segments)")

    def filter_wall_lines(self):
        """Filter lines that are likely walls"""
        print("Filtering for wall-like lines...")

        for line in self.all_lines:
            # Check length
            if line['length'] < self.min_wall_length:
                continue

            # Check if roughly horizontal or vertical
            angle = line['angle']
            is_horizontal = angle < self.angle_tolerance or angle > (180 - self.angle_tolerance)
            is_vertical = abs(angle - 90) < self.angle_tolerance

            if not (is_horizontal or is_vertical):
                continue  # Skip diagonal lines for now

            # Check line width (walls are usually drawn with specific thickness)
            # But be lenient since PDF line widths vary

            line['is_horizontal'] = is_horizontal
            line['is_vertical'] = is_vertical
            self.wall_lines.append(line)

        print(f"  Filtered to {len(self.wall_lines)} potential wall lines")

        # Separate by orientation
        h_lines = [l for l in self.wall_lines if l.get('is_horizontal')]
        v_lines = [l for l in self.wall_lines if l.get('is_vertical')]
        print(f"  Horizontal: {len(h_lines)}, Vertical: {len(v_lines)}")

    def detect_scale(self):
        """Try to auto-detect scale from drawing"""
        # Look for typical architectural scales
        # For now, use a default based on standard architectural sheet
        # Typical 24x36 sheet at 1/4" = 1'-0" scale

        # Assuming standard ARCH D sheet (24" x 36" = 1728 x 2592 points at 72 dpi)
        # At 1/4" = 1'-0", 1 foot = 0.25" = 18 points

        # Use the page dimensions to estimate
        # If page is ~792 x 612 (letter) or ~1224 x 792 (tabloid), adjust accordingly

        if self.page_width > 1500:  # Large format (likely ARCH D or similar)
            self.scale_factor = 18  # points per foot at 1/4" = 1'-0"
        elif self.page_width > 1000:  # Tabloid-ish
            self.scale_factor = 12  # points per foot at 1/8" = 1'-0"
        else:  # Letter size
            self.scale_factor = 6  # points per foot at 1/16" = 1'-0"

        print(f"  Estimated scale: {self.scale_factor} points/foot")
        print(f"  (This means 1 foot = {self.scale_factor} PDF points)")

    def find_wall_clusters(self):
        """Group nearby parallel lines into wall centerlines"""
        print("Clustering wall lines...")

        # For thick walls, there might be two parallel lines (inner and outer face)
        # We want to find the centerline

        h_lines = sorted([l for l in self.wall_lines if l.get('is_horizontal')],
                        key=lambda x: (x['start'][1] + x['end'][1]) / 2)
        v_lines = sorted([l for l in self.wall_lines if l.get('is_vertical')],
                        key=lambda x: (x['start'][0] + x['end'][0]) / 2)

        # Cluster horizontal lines by Y position
        h_clusters = self._cluster_lines(h_lines, 'y')
        v_clusters = self._cluster_lines(v_lines, 'x')

        print(f"  Found {len(h_clusters)} horizontal wall clusters")
        print(f"  Found {len(v_clusters)} vertical wall clusters")

        # Convert clusters to wall segments
        for cluster in h_clusters:
            segment = self._cluster_to_segment(cluster, 'horizontal')
            if segment:
                self.wall_segments.append(segment)

        for cluster in v_clusters:
            segment = self._cluster_to_segment(cluster, 'vertical')
            if segment:
                self.wall_segments.append(segment)

        print(f"  Generated {len(self.wall_segments)} wall segments")

    def _cluster_lines(self, lines, axis):
        """Cluster lines by position on given axis"""
        if not lines:
            return []

        clusters = []
        current_cluster = [lines[0]]

        for line in lines[1:]:
            if axis == 'y':
                current_pos = (current_cluster[-1]['start'][1] + current_cluster[-1]['end'][1]) / 2
                new_pos = (line['start'][1] + line['end'][1]) / 2
            else:
                current_pos = (current_cluster[-1]['start'][0] + current_cluster[-1]['end'][0]) / 2
                new_pos = (line['start'][0] + line['end'][0]) / 2

            if abs(new_pos - current_pos) < self.snap_distance * 2:
                current_cluster.append(line)
            else:
                if len(current_cluster) >= 1:  # Keep single lines too
                    clusters.append(current_cluster)
                current_cluster = [line]

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    def _cluster_to_segment(self, cluster, orientation):
        """Convert a cluster of lines to a single wall segment"""
        if not cluster:
            return None

        # Find the extent of all lines in cluster
        all_x = []
        all_y = []

        for line in cluster:
            all_x.extend([line['start'][0], line['end'][0]])
            all_y.extend([line['start'][1], line['end'][1]])

        if orientation == 'horizontal':
            # Horizontal wall: same Y, varying X
            y = sum(all_y) / len(all_y)
            x1, x2 = min(all_x), max(all_x)
            return {
                'start': (x1, y),
                'end': (x2, y),
                'orientation': 'horizontal',
                'length_pts': x2 - x1
            }
        else:
            # Vertical wall: same X, varying Y
            x = sum(all_x) / len(all_x)
            y1, y2 = min(all_y), max(all_y)
            return {
                'start': (x, y1),
                'end': (x, y2),
                'orientation': 'vertical',
                'length_pts': y2 - y1
            }

    def filter_by_length(self, min_feet=2):
        """Remove walls shorter than minimum length"""
        if not self.scale_factor:
            return

        min_pts = min_feet * self.scale_factor
        before = len(self.wall_segments)
        self.wall_segments = [w for w in self.wall_segments if w['length_pts'] >= min_pts]
        print(f"  Filtered walls >= {min_feet}ft: {before} -> {len(self.wall_segments)}")

    def snap_endpoints(self):
        """Snap nearby endpoints together for clean intersections"""
        print("Snapping wall endpoints...")

        # Collect all endpoints
        endpoints = []
        for i, wall in enumerate(self.wall_segments):
            endpoints.append(('start', i, wall['start']))
            endpoints.append(('end', i, wall['end']))

        # Find clusters of nearby points
        snap_groups = []
        used = set()

        for i, (type1, wall_idx1, pt1) in enumerate(endpoints):
            if i in used:
                continue
            group = [(type1, wall_idx1, pt1)]
            used.add(i)

            for j, (type2, wall_idx2, pt2) in enumerate(endpoints):
                if j in used:
                    continue
                dist = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if dist < self.snap_distance:
                    group.append((type2, wall_idx2, pt2))
                    used.add(j)

            if len(group) > 1:
                snap_groups.append(group)

        # Snap points to average position
        for group in snap_groups:
            avg_x = sum(p[2][0] for p in group) / len(group)
            avg_y = sum(p[2][1] for p in group) / len(group)

            for type_, wall_idx, _ in group:
                if type_ == 'start':
                    self.wall_segments[wall_idx]['start'] = (avg_x, avg_y)
                else:
                    self.wall_segments[wall_idx]['end'] = (avg_x, avg_y)

        print(f"  Snapped {len(snap_groups)} endpoint groups")

    def convert_to_feet(self):
        """Convert all coordinates from PDF points to feet"""
        if not self.scale_factor:
            print("Warning: Scale not set, using raw PDF coordinates")
            return

        for wall in self.wall_segments:
            wall['start_ft'] = (
                wall['start'][0] / self.scale_factor,
                wall['start'][1] / self.scale_factor
            )
            wall['end_ft'] = (
                wall['end'][0] / self.scale_factor,
                wall['end'][1] / self.scale_factor
            )
            wall['length_ft'] = wall['length_pts'] / self.scale_factor

    def normalize_origin(self):
        """Move origin to bottom-left of building"""
        if not self.wall_segments:
            return

        # Find bounds
        all_x = []
        all_y = []
        for wall in self.wall_segments:
            if 'start_ft' in wall:
                all_x.extend([wall['start_ft'][0], wall['end_ft'][0]])
                all_y.extend([wall['start_ft'][1], wall['end_ft'][1]])

        if not all_x:
            return

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        print(f"  Building bounds: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}] ft")
        print(f"  Building size: {max_x - min_x:.1f} x {max_y - min_y:.1f} ft")

        # Normalize: origin at min, flip Y (PDF Y is top-down, Revit Y is bottom-up)
        for wall in self.wall_segments:
            if 'start_ft' in wall:
                wall['revit_start'] = (
                    round(wall['start_ft'][0] - min_x, 4),
                    round(max_y - wall['start_ft'][1], 4)  # Flip Y
                )
                wall['revit_end'] = (
                    round(wall['end_ft'][0] - min_x, 4),
                    round(max_y - wall['end_ft'][1], 4)  # Flip Y
                )

    def generate_revit_commands(self, level_id=30, wall_height=10):
        """Generate Revit MCP commands for creating walls"""
        commands = []

        for wall in self.wall_segments:
            if 'revit_start' not in wall:
                continue

            cmd = {
                'method': 'createWall',
                'params': {
                    'startPoint': [wall['revit_start'][0], wall['revit_start'][1], 0],
                    'endPoint': [wall['revit_end'][0], wall['revit_end'][1], 0],
                    'levelId': level_id,
                    'height': wall_height
                }
            }
            commands.append(cmd)

        return commands

    def export_results(self, output_path=None):
        """Export detection results to JSON"""
        if output_path is None:
            output_path = Path(self.pdf_path).stem + "_auto_walls.json"

        results = {
            'source_pdf': str(self.pdf_path),
            'page_number': self.page_num,
            'timestamp': datetime.now().isoformat(),
            'detection_params': {
                'min_wall_length': self.min_wall_length,
                'angle_tolerance': self.angle_tolerance,
                'snap_distance': self.snap_distance,
                'scale_factor': self.scale_factor
            },
            'stats': {
                'total_lines_found': len(self.all_lines),
                'wall_lines_filtered': len(self.wall_lines),
                'wall_segments_created': len(self.wall_segments)
            },
            'walls': [],
            'revit_commands': []
        }

        for i, wall in enumerate(self.wall_segments):
            wall_data = {
                'id': i + 1,
                'orientation': wall.get('orientation'),
                'pdf_start': wall['start'],
                'pdf_end': wall['end'],
                'length_pts': round(wall['length_pts'], 2)
            }
            if 'revit_start' in wall:
                wall_data['revit_start'] = wall['revit_start']
                wall_data['revit_end'] = wall['revit_end']
                wall_data['length_ft'] = round(wall.get('length_ft', 0), 2)
            results['walls'].append(wall_data)

        results['revit_commands'] = self.generate_revit_commands()

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nExported to: {output_path}")
        return results

    def run_detection(self, min_wall_feet=2, scale_pts_per_foot=None):
        """Run the full detection pipeline"""
        print(f"\n{'='*60}")
        print(f"Auto Wall Detection: {Path(self.pdf_path).name}")
        print(f"{'='*60}\n")

        self.load_pdf()
        self.extract_lines()
        self.filter_wall_lines()

        if scale_pts_per_foot:
            self.scale_factor = scale_pts_per_foot
            print(f"Using provided scale: {self.scale_factor} pts/ft")
        else:
            self.detect_scale()

        self.find_wall_clusters()
        self.filter_by_length(min_wall_feet)
        self.snap_endpoints()
        self.convert_to_feet()
        self.normalize_origin()

        results = self.export_results()

        print(f"\n{'='*60}")
        print(f"Detection Complete!")
        print(f"  Found {len(self.wall_segments)} wall segments")
        print(f"  Generated {len(results['revit_commands'])} Revit commands")
        print(f"{'='*60}\n")

        return results


def show_preview(pdf_path, page_num, walls):
    """Show a preview of detected walls overlaid on PDF"""
    try:
        import tkinter as tk
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        print("Preview requires Pillow and tkinter")
        return

    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render PDF
    mat = fitz.Matrix(1.5, 1.5)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Draw walls on image
    draw = ImageDraw.Draw(img)
    scale = 1.5  # Match the matrix scale

    for wall in walls:
        x1, y1 = wall['start'][0] * scale, wall['start'][1] * scale
        x2, y2 = wall['end'][0] * scale, wall['end'][1] * scale
        draw.line([(x1, y1), (x2, y2)], fill='red', width=3)
        # Draw endpoints
        draw.ellipse([x1-4, y1-4, x1+4, y1+4], fill='blue')
        draw.ellipse([x2-4, y2-4, x2+4, y2+4], fill='blue')

    # Show in window
    root = tk.Tk()
    root.title("Detected Walls Preview")

    # Create scrollable canvas
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, width=min(img.width, 1400), height=min(img.height, 900))
    h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)

    canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    photo = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.config(scrollregion=(0, 0, img.width, img.height))

    # Info label
    info = tk.Label(root, text=f"Detected {len(walls)} walls. Close window to continue.",
                   font=('Arial', 12))
    info.pack(pady=5)

    root.mainloop()


def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_wall_detect.py <pdf_path> [page_number] [scale_pts_per_foot]")
        print("\nExample:")
        print("  python auto_wall_detect.py floor_plan.pdf 6 18")
        print("\nScale reference (at 72 DPI):")
        print("  1/4\" = 1'-0\"  -> 18 pts/ft")
        print("  1/8\" = 1'-0\"  -> 9 pts/ft")
        print("  3/16\" = 1'-0\" -> 13.5 pts/ft")
        return

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else None

    detector = AutoWallDetector(pdf_path, page_num)
    results = detector.run_detection(min_wall_feet=2, scale_pts_per_foot=scale)

    # Show preview
    if detector.wall_segments:
        show_preview(pdf_path, page_num, detector.wall_segments)

    # Print Revit commands
    print("\n" + "="*60)
    print("REVIT WALL COMMANDS:")
    print("="*60)
    for cmd in results['revit_commands'][:10]:  # Show first 10
        print(json.dumps(cmd, indent=2))
    if len(results['revit_commands']) > 10:
        print(f"... and {len(results['revit_commands']) - 10} more")


if __name__ == "__main__":
    main()

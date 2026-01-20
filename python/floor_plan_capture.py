"""
Floor Plan Coordinate Capture Tool

This tool allows you to:
1. Open a PDF floor plan
2. Click on wall corners/endpoints
3. Set a scale reference (two points with known distance)
4. Export coordinates in feet for Revit wall creation

Usage:
    python floor_plan_capture.py <pdf_path> [page_number]

Controls:
    Left Click  - Add a point
    Right Click - Remove last point
    S           - Set scale (click two points, enter distance)
    W           - Start new wall chain
    G           - Add grid line
    E           - Export to JSON
    C           - Clear all points
    Z           - Undo last point
    Q/Esc       - Quit
    Arrow Keys  - Pan view
    +/-         - Zoom in/out
"""

import sys
import json
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Installing PyMuPDF...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
    import fitz

from PIL import Image, ImageTk


class FloorPlanCapture:
    def __init__(self, pdf_path, page_num=0):
        self.pdf_path = pdf_path
        self.page_num = page_num

        # Coordinate data
        self.points = []  # All captured points
        self.walls = []   # Wall chains (list of point lists)
        self.current_wall = []  # Current wall being drawn
        self.grid_lines = []  # Grid lines

        # Scale calibration
        self.scale_points = []  # Two points for scale reference
        self.scale_factor = None  # Pixels per foot
        self.scale_distance = None  # Known distance in feet

        # View state
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Mode
        self.mode = "wall"  # wall, scale, grid

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title(f"Floor Plan Capture - {Path(self.pdf_path).name}")

        # Create main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbars
        self.canvas_frame = tk.Frame(main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=1200,
            height=800,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            bg='gray'
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        # Create info panel
        self.info_frame = tk.Frame(main_frame, width=300, bg='#f0f0f0')
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_frame.pack_propagate(False)

        # Info labels
        tk.Label(self.info_frame, text="Floor Plan Capture", font=('Arial', 14, 'bold'), bg='#f0f0f0').pack(pady=10)

        self.mode_label = tk.Label(self.info_frame, text="Mode: WALL", font=('Arial', 12), bg='#f0f0f0', fg='blue')
        self.mode_label.pack(pady=5)

        self.scale_label = tk.Label(self.info_frame, text="Scale: Not Set", font=('Arial', 10), bg='#f0f0f0')
        self.scale_label.pack(pady=5)

        self.point_count_label = tk.Label(self.info_frame, text="Points: 0", font=('Arial', 10), bg='#f0f0f0')
        self.point_count_label.pack(pady=5)

        self.wall_count_label = tk.Label(self.info_frame, text="Walls: 0", font=('Arial', 10), bg='#f0f0f0')
        self.wall_count_label.pack(pady=5)

        self.coords_label = tk.Label(self.info_frame, text="Cursor: (-, -)", font=('Arial', 10), bg='#f0f0f0')
        self.coords_label.pack(pady=5)

        self.feet_label = tk.Label(self.info_frame, text="Feet: (-, -)", font=('Arial', 10), bg='#f0f0f0')
        self.feet_label.pack(pady=5)

        # Buttons
        tk.Label(self.info_frame, text="─" * 30, bg='#f0f0f0').pack(pady=10)

        btn_frame = tk.Frame(self.info_frame, bg='#f0f0f0')
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Set Scale (S)", command=self.start_scale_mode, width=15).pack(pady=2)
        tk.Button(btn_frame, text="New Wall (W)", command=self.start_new_wall, width=15).pack(pady=2)
        tk.Button(btn_frame, text="Add Grid (G)", command=self.start_grid_mode, width=15).pack(pady=2)
        tk.Button(btn_frame, text="Undo (Z)", command=self.undo_last, width=15).pack(pady=2)
        tk.Button(btn_frame, text="Clear All (C)", command=self.clear_all, width=15).pack(pady=2)
        tk.Button(btn_frame, text="Export JSON (E)", command=self.export_json, width=15).pack(pady=2)

        tk.Label(self.info_frame, text="─" * 30, bg='#f0f0f0').pack(pady=10)

        # Instructions
        instructions = """
Controls:
• Left Click: Add point
• Right Click: End wall chain
• S: Set scale mode
• W: New wall chain
• G: Grid line mode
• Z: Undo last point
• C: Clear all
• E: Export to JSON
• Mouse wheel: Zoom
• Middle drag: Pan

Scale Setup:
1. Press 'S'
2. Click two points
3. Enter known distance
        """
        tk.Label(self.info_frame, text=instructions, font=('Arial', 9), bg='#f0f0f0', justify=tk.LEFT).pack(pady=10)

        # Point list
        tk.Label(self.info_frame, text="Recent Points:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(pady=5)

        self.points_listbox = tk.Listbox(self.info_frame, height=10, width=35)
        self.points_listbox.pack(pady=5, padx=5)

        # Bind events
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-2>', self.start_pan)
        self.canvas.bind('<B2-Motion>', self.do_pan)

        self.root.bind('<Key>', self.on_key)

        # Load PDF
        self.load_pdf()

    def load_pdf(self):
        """Load PDF and display on canvas"""
        try:
            self.doc = fitz.open(self.pdf_path)
            self.page = self.doc[self.page_num]

            # Render at high resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = self.page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.original_image = img
            self.image_width = img.width
            self.image_height = img.height

            # Store PDF dimensions for scale calculation
            self.pdf_width = self.page.rect.width
            self.pdf_height = self.page.rect.height
            self.render_scale = 2.0  # The matrix scale we used

            self.display_image()

            # Set scroll region
            self.canvas.config(scrollregion=(0, 0, self.image_width, self.image_height))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")

    def display_image(self):
        """Display the PDF image on canvas"""
        # Apply zoom
        new_width = int(self.image_width * self.zoom)
        new_height = int(self.image_height * self.zoom)

        resized = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))

        # Redraw all captured elements
        self.redraw_elements()

    def redraw_elements(self):
        """Redraw all captured points, walls, and grid lines"""
        # Draw completed walls
        for wall_chain in self.walls:
            if len(wall_chain) >= 2:
                for i in range(len(wall_chain) - 1):
                    p1 = wall_chain[i]
                    p2 = wall_chain[i + 1]
                    x1, y1 = p1['px'] * self.zoom, p1['py'] * self.zoom
                    x2, y2 = p2['px'] * self.zoom, p2['py'] * self.zoom
                    self.canvas.create_line(x1, y1, x2, y2, fill='blue', width=2, tags='wall')

            # Draw points
            for pt in wall_chain:
                x, y = pt['px'] * self.zoom, pt['py'] * self.zoom
                self.canvas.create_oval(x-4, y-4, x+4, y+4, fill='blue', outline='white', tags='point')

        # Draw current wall chain
        if len(self.current_wall) >= 1:
            for i, pt in enumerate(self.current_wall):
                x, y = pt['px'] * self.zoom, pt['py'] * self.zoom
                self.canvas.create_oval(x-5, y-5, x+5, y+5, fill='red', outline='white', tags='current')

                if i > 0:
                    prev = self.current_wall[i-1]
                    px, py = prev['px'] * self.zoom, prev['py'] * self.zoom
                    self.canvas.create_line(px, py, x, y, fill='red', width=2, tags='current')

        # Draw scale points
        for pt in self.scale_points:
            x, y = pt['px'] * self.zoom, pt['py'] * self.zoom
            self.canvas.create_oval(x-6, y-6, x+6, y+6, fill='green', outline='white', width=2, tags='scale')

        if len(self.scale_points) == 2:
            p1, p2 = self.scale_points
            x1, y1 = p1['px'] * self.zoom, p1['py'] * self.zoom
            x2, y2 = p2['px'] * self.zoom, p2['py'] * self.zoom
            self.canvas.create_line(x1, y1, x2, y2, fill='green', width=2, dash=(5, 5), tags='scale')

        # Draw grid lines
        for grid in self.grid_lines:
            if len(grid) == 2:
                p1, p2 = grid
                x1, y1 = p1['px'] * self.zoom, p1['py'] * self.zoom
                x2, y2 = p2['px'] * self.zoom, p2['py'] * self.zoom
                self.canvas.create_line(x1, y1, x2, y2, fill='orange', width=1, dash=(10, 5), tags='grid')

    def on_left_click(self, event):
        """Handle left click - add point"""
        # Get canvas coordinates
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # Convert to image coordinates (account for zoom)
        px = cx / self.zoom
        py = cy / self.zoom

        # Calculate feet coordinates if scale is set
        feet_x, feet_y = None, None
        if self.scale_factor:
            feet_x = px / self.scale_factor
            feet_y = py / self.scale_factor

        point = {
            'px': px,
            'py': py,
            'feet_x': feet_x,
            'feet_y': feet_y
        }

        if self.mode == "scale":
            self.scale_points.append(point)
            if len(self.scale_points) == 2:
                self.prompt_scale_distance()
            self.display_image()

        elif self.mode == "wall":
            self.current_wall.append(point)
            self.update_info()
            self.display_image()

        elif self.mode == "grid":
            if not hasattr(self, 'current_grid'):
                self.current_grid = []
            self.current_grid.append(point)
            if len(self.current_grid) == 2:
                self.grid_lines.append(self.current_grid)
                self.current_grid = []
            self.display_image()

    def on_right_click(self, event):
        """Handle right click - end current wall chain"""
        if self.current_wall:
            self.walls.append(self.current_wall)
            self.current_wall = []
            self.update_info()
            self.display_image()

    def on_mouse_move(self, event):
        """Update cursor position display"""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        px = cx / self.zoom
        py = cy / self.zoom

        self.coords_label.config(text=f"Pixels: ({px:.1f}, {py:.1f})")

        if self.scale_factor:
            feet_x = px / self.scale_factor
            feet_y = py / self.scale_factor
            self.feet_label.config(text=f"Feet: ({feet_x:.2f}, {feet_y:.2f})")
        else:
            self.feet_label.config(text="Feet: (Set scale first)")

    def on_mouse_wheel(self, event):
        """Zoom with mouse wheel"""
        if event.delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1
        self.zoom = max(0.1, min(5.0, self.zoom))
        self.display_image()

    def start_pan(self, event):
        """Start panning"""
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        """Pan the view"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_key(self, event):
        """Handle keyboard shortcuts"""
        key = event.keysym.lower()

        if key == 's':
            self.start_scale_mode()
        elif key == 'w':
            self.start_new_wall()
        elif key == 'g':
            self.start_grid_mode()
        elif key == 'z':
            self.undo_last()
        elif key == 'c':
            self.clear_all()
        elif key == 'e':
            self.export_json()
        elif key in ('q', 'escape'):
            self.root.quit()

    def start_scale_mode(self):
        """Enter scale calibration mode"""
        self.mode = "scale"
        self.scale_points = []
        self.mode_label.config(text="Mode: SCALE", fg='green')
        messagebox.showinfo("Scale Mode", "Click two points with a known distance between them.")

    def start_new_wall(self):
        """Start a new wall chain"""
        if self.current_wall:
            self.walls.append(self.current_wall)
        self.current_wall = []
        self.mode = "wall"
        self.mode_label.config(text="Mode: WALL", fg='blue')
        self.update_info()
        self.display_image()

    def start_grid_mode(self):
        """Enter grid line mode"""
        self.mode = "grid"
        self.current_grid = []
        self.mode_label.config(text="Mode: GRID", fg='orange')
        messagebox.showinfo("Grid Mode", "Click two points to define a grid line.")

    def prompt_scale_distance(self):
        """Ask user for the distance between scale points"""
        distance = simpledialog.askfloat(
            "Scale Distance",
            "Enter the distance between the two points (in feet):",
            minvalue=0.1
        )

        if distance:
            # Calculate pixel distance
            p1, p2 = self.scale_points
            pixel_dist = ((p2['px'] - p1['px'])**2 + (p2['py'] - p1['py'])**2)**0.5

            self.scale_factor = pixel_dist / distance
            self.scale_distance = distance
            self.scale_label.config(text=f"Scale: {self.scale_factor:.2f} px/ft")

            # Update all existing points with feet coordinates
            self.recalculate_feet_coords()

            messagebox.showinfo("Scale Set", f"Scale calibrated: {self.scale_factor:.2f} pixels per foot")

        self.mode = "wall"
        self.mode_label.config(text="Mode: WALL", fg='blue')

    def recalculate_feet_coords(self):
        """Recalculate feet coordinates for all points"""
        if not self.scale_factor:
            return

        for wall in self.walls:
            for pt in wall:
                pt['feet_x'] = pt['px'] / self.scale_factor
                pt['feet_y'] = pt['py'] / self.scale_factor

        for pt in self.current_wall:
            pt['feet_x'] = pt['px'] / self.scale_factor
            pt['feet_y'] = pt['py'] / self.scale_factor

    def undo_last(self):
        """Undo last point"""
        if self.current_wall:
            self.current_wall.pop()
        elif self.walls:
            self.current_wall = self.walls.pop()
            if self.current_wall:
                self.current_wall.pop()
        self.update_info()
        self.display_image()

    def clear_all(self):
        """Clear all captured data"""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all captured points?"):
            self.points = []
            self.walls = []
            self.current_wall = []
            self.grid_lines = []
            self.update_info()
            self.display_image()

    def update_info(self):
        """Update info panel"""
        total_points = sum(len(w) for w in self.walls) + len(self.current_wall)
        self.point_count_label.config(text=f"Points: {total_points}")
        self.wall_count_label.config(text=f"Walls: {len(self.walls)} (+{len(self.current_wall)} current)")

        # Update points listbox
        self.points_listbox.delete(0, tk.END)

        # Show current wall points
        for i, pt in enumerate(self.current_wall[-5:]):  # Last 5 points
            if pt.get('feet_x') is not None:
                text = f"  ({pt['feet_x']:.2f}, {pt['feet_y']:.2f}) ft"
            else:
                text = f"  ({pt['px']:.1f}, {pt['py']:.1f}) px"
            self.points_listbox.insert(tk.END, text)

    def export_json(self):
        """Export captured data to JSON"""
        if self.current_wall:
            self.walls.append(self.current_wall)
            self.current_wall = []

        if not self.walls and not self.grid_lines:
            messagebox.showwarning("No Data", "No walls or grid lines to export.")
            return

        # Prepare export data
        export_data = {
            'source_pdf': str(self.pdf_path),
            'page_number': self.page_num,
            'timestamp': datetime.now().isoformat(),
            'scale': {
                'pixels_per_foot': self.scale_factor,
                'reference_distance_feet': self.scale_distance
            },
            'walls': [],
            'grid_lines': []
        }

        # Export walls
        for i, wall in enumerate(self.walls):
            wall_data = {
                'wall_id': i + 1,
                'points': []
            }
            for pt in wall:
                point_data = {
                    'pixel_x': pt['px'],
                    'pixel_y': pt['py']
                }
                if pt.get('feet_x') is not None:
                    point_data['feet_x'] = round(pt['feet_x'], 4)
                    point_data['feet_y'] = round(pt['feet_y'], 4)
                wall_data['points'].append(point_data)
            export_data['walls'].append(wall_data)

        # Export grid lines
        for i, grid in enumerate(self.grid_lines):
            grid_data = {
                'grid_id': i + 1,
                'points': []
            }
            for pt in grid:
                point_data = {
                    'pixel_x': pt['px'],
                    'pixel_y': pt['py']
                }
                if pt.get('feet_x') is not None:
                    point_data['feet_x'] = round(pt['feet_x'], 4)
                    point_data['feet_y'] = round(pt['feet_y'], 4)
                grid_data['points'].append(point_data)
            export_data['grid_lines'].append(grid_data)

        # Generate Revit wall commands
        if self.scale_factor:
            export_data['revit_commands'] = self.generate_revit_commands()

        # Save file
        default_name = Path(self.pdf_path).stem + "_walls.json"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=default_name
        )

        if save_path:
            with open(save_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            messagebox.showinfo("Exported", f"Data exported to:\n{save_path}")
            print(f"\nExported to: {save_path}")
            print(json.dumps(export_data, indent=2))

    def generate_revit_commands(self):
        """Generate Revit wall creation commands"""
        commands = []

        # Find the origin point (minimum x and y)
        all_points = []
        for wall in self.walls:
            for pt in wall:
                if pt.get('feet_x') is not None:
                    all_points.append((pt['feet_x'], pt['feet_y']))

        if not all_points:
            return commands

        # Use min point as origin
        min_x = min(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)

        # Note: PDF Y-axis is inverted (top-down), so we flip Y
        max_y = max(p[1] for p in all_points)

        for wall in self.walls:
            for i in range(len(wall) - 1):
                p1 = wall[i]
                p2 = wall[i + 1]

                if p1.get('feet_x') is None or p2.get('feet_x') is None:
                    continue

                # Convert to Revit coordinates (origin at min, Y flipped)
                x1 = round(p1['feet_x'] - min_x, 4)
                y1 = round(max_y - p1['feet_y'], 4)  # Flip Y
                x2 = round(p2['feet_x'] - min_x, 4)
                y2 = round(max_y - p2['feet_y'], 4)  # Flip Y

                cmd = {
                    'method': 'createWall',
                    'params': {
                        'startPoint': [x1, y1, 0],
                        'endPoint': [x2, y2, 0],
                        'levelId': 30,  # L1
                        'height': 10
                    }
                }
                commands.append(cmd)

        return commands

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    if len(sys.argv) < 2:
        # Open file dialog
        root = tk.Tk()
        root.withdraw()
        pdf_path = filedialog.askopenfilename(
            title="Select PDF Floor Plan",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        root.destroy()

        if not pdf_path:
            print("No file selected.")
            return
    else:
        pdf_path = sys.argv[1]

    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"Opening: {pdf_path}, page {page_num}")

    app = FloorPlanCapture(pdf_path, page_num)
    app.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Split the floor plan image into quadrants for detailed analysis
"""

from PIL import Image
import os

def split_into_quadrants(image_path, output_dir, grid_rows=3, grid_cols=4):
    """
    Split image into a grid of quadrants

    For this floor plan sheet:
    - Left half = 1ST FLOOR PLAN
    - Right half = 2ND FLOOR PLAN
    - Use 3 rows x 4 cols to get good detail

    Returns paths to all quadrant images
    """
    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(image_path)
    width, height = img.size
    print(f"Original image: {width} x {height} pixels")

    quad_width = width // grid_cols
    quad_height = height // grid_rows

    print(f"Quadrant size: {quad_width} x {quad_height} pixels")
    print(f"Grid: {grid_rows} rows x {grid_cols} columns = {grid_rows * grid_cols} quadrants")

    quadrants = []

    for row in range(grid_rows):
        for col in range(grid_cols):
            # Calculate bounds
            left = col * quad_width
            upper = row * quad_height
            right = left + quad_width
            lower = upper + quad_height

            # Crop quadrant
            quad = img.crop((left, upper, right, lower))

            # Save with descriptive name
            # Row 0 = top, Row 2 = bottom
            # Col 0 = left (1st floor), Col 2-3 = right (2nd floor)
            row_name = ["top", "middle", "bottom"][row]
            col_name = ["1stFL_left", "1stFL_right", "2ndFL_left", "2ndFL_right"][col]

            filename = f"q_{row}_{col}_{row_name}_{col_name}.png"
            filepath = os.path.join(output_dir, filename)
            quad.save(filepath)

            quadrants.append({
                "row": row,
                "col": col,
                "row_name": row_name,
                "col_name": col_name,
                "filepath": filepath,
                "bounds": {
                    "left": left,
                    "upper": upper,
                    "right": right,
                    "lower": lower
                }
            })

            print(f"  Saved: {filename}")

    # Also create the 1st floor only (left half)
    half_width = width // 2
    first_floor = img.crop((0, 0, half_width, height))
    first_floor_path = os.path.join(output_dir, "1st_floor_only.png")
    first_floor.save(first_floor_path)
    print(f"\n  Saved: 1st_floor_only.png (left half)")

    # Create 1st floor split into 3x2 grid for more detail
    fp_width = half_width
    fp_height = height

    fp_quad_width = fp_width // 2
    fp_quad_height = fp_height // 3

    print(f"\n1st Floor Detail Grid (3x2):")
    for row in range(3):
        for col in range(2):
            left = col * fp_quad_width
            upper = row * fp_quad_height
            right = left + fp_quad_width
            lower = upper + fp_quad_height

            quad = first_floor.crop((left, upper, right, lower))

            row_name = ["north", "center", "south"][row]
            col_name = ["west", "east"][col]

            filename = f"1stFL_detail_{row}_{col}_{row_name}_{col_name}.png"
            filepath = os.path.join(output_dir, filename)
            quad.save(filepath)
            print(f"  Saved: {filename}")

    img.close()
    first_floor.close()

    return quadrants


if __name__ == "__main__":
    image_path = "/mnt/d/RevitMCPBridge2026/floor_plan_A100.png"
    output_dir = "/mnt/d/RevitMCPBridge2026/floor_plan_quadrants"

    print("=" * 60)
    print("FLOOR PLAN QUADRANT SPLITTER")
    print("=" * 60)

    quadrants = split_into_quadrants(image_path, output_dir)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")
    print(f"Total quadrants: {len(quadrants)}")
    print("\nNow read each quadrant image to analyze the floor plan section by section.")

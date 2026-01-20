#!/usr/bin/env python3
"""Test the boundary tracer on 4020 Woodside Drive floor plan."""

import sys
sys.path.insert(0, '/mnt/d/RevitMCPBridge2026/floor-plan-vision-mcp/src')

from floor_plan_vision.extractor import extract_geometry
from floor_plan_vision.boundary_tracer import trace_boundaries, BoundaryTracer
from floor_plan_vision.text_extractor import extract_text
import json

# PDF path
pdf_path = "/mnt/d/010 - LATEST PROJECT PDF FILES - PORT/2024 - 4020 Woodside Drive - Architecture.pdf"
page_num = 5

print(f"Extracting geometry from page {page_num}...")
geometry = extract_geometry(pdf_path, page_num)
print(f"  Lines: {len(geometry.get('lines', []))}")

print("\nExtracting text/room labels...")
text = extract_text(geometry)
rooms = text.get('rooms', [])
print(f"  Room labels found: {len(rooms)}")

print("\nTracing boundaries...")
result = trace_boundaries(geometry, rooms)
print(f"  Boundaries found: {result['boundary_count']}")
print(f"  Room boundaries: {result['room_count']}")
print(f"  Total room area: {result['total_area_sqft']:.1f} sqft")

print("\nBoundary details:")
for i, boundary in enumerate(result.get('boundaries', [])[:15]):
    btype = boundary['boundary_type']
    name = boundary.get('room_name', '')
    area = boundary['area_sqft']
    pts = boundary['point_count']
    print(f"  {i+1}. [{btype}] {name or 'Unnamed'}: {area:.1f} sqft, {pts} points")

if result.get('exterior_boundary'):
    ext = result['exterior_boundary']
    print(f"\nExterior boundary: {ext['area_sqft']:.1f} sqft, {ext['point_count']} points")

# Save results
with open('/mnt/d/RevitMCPBridge2026/traced_boundaries.json', 'w') as f:
    json.dump(result, f, indent=2)
print("\nResults saved to traced_boundaries.json")

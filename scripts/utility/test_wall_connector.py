#!/usr/bin/env python3
"""Test the wall connector on 4020 Woodside Drive floor plan."""

import sys
sys.path.insert(0, '/mnt/d/RevitMCPBridge2026/floor-plan-vision-mcp/src')

from floor_plan_vision.extractor import extract_geometry
from floor_plan_vision.wall_detector import detect_walls
from floor_plan_vision.wall_connector import connect_walls
from floor_plan_vision.text_extractor import extract_text
import json

# PDF path
pdf_path = "/mnt/d/010 - LATEST PROJECT PDF FILES - PORT/2024 - 4020 Woodside Drive - Architecture.pdf"
page_num = 5

print(f"Extracting geometry from page {page_num}...")
geometry = extract_geometry(pdf_path, page_num)
print(f"  Lines: {len(geometry.get('lines', []))}")
print(f"  Texts: {len(geometry.get('texts', []))}")

print("\nDetecting walls...")
walls = detect_walls(geometry)
print(f"  Wall count: {walls['wall_count']}")
print(f"  Exterior: {walls['exterior_count']}")
print(f"  Interior: {walls['interior_count']}")

print("\nExtracting text/room labels...")
text = extract_text(geometry)
rooms = text.get('rooms', [])
print(f"  Room labels found: {len(rooms)}")
for room in rooms[:5]:
    print(f"    - {room.get('name', 'Unknown')}")
if len(rooms) > 5:
    print(f"    ... and {len(rooms) - 5} more")

print("\nConnecting walls into chains...")
connected = connect_walls(walls, rooms)
print(f"  Chain count: {connected['chain_count']}")
print(f"  Closed chains (rooms): {connected['closed_chains']}")
print(f"  Open chains: {connected['open_chains']}")
print(f"  Detected rooms: {connected['room_count']}")

print("\nChain details:")
for i, chain in enumerate(connected.get('chains', [])[:10]):
    status = "CLOSED" if chain['is_closed'] else "open"
    room = chain.get('room_name', '')
    print(f"  Chain {i+1}: {chain['segment_count']} segments, {chain['total_length']:.1f} pts, {status} {room}")

print("\nRoom boundaries:")
for room in connected.get('rooms', []):
    print(f"  - {room['name']}: {room.get('area_sqft', 0):.1f} sqft")

# Save results for inspection
with open('/mnt/d/RevitMCPBridge2026/connected_walls_test.json', 'w') as f:
    json.dump(connected, f, indent=2)
print("\nResults saved to connected_walls_test.json")

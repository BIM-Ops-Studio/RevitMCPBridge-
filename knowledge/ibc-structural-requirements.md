# IBC Structural Requirements

**Based on**: IBC 2021 Chapter 16, ASCE 7-16
**Reference Standards**: ACI 318, AISC 360, NDS, TMS 402

---

## Quick Reference - Common Load Values

### Minimum Uniformly Distributed Live Loads (Table 1607.1)

| Occupancy/Use | Live Load (psf) |
|---------------|-----------------|
| **Residential** | |
| Dwelling units | 40 |
| Hotels/motels - Private rooms | 40 |
| Hotels/motels - Public rooms | 100 |
| Habitable attics | 30 |
| Uninhabitable attics (storage) | 20 |
| Uninhabitable attics (no storage) | 10 |
| Balconies - Exterior (residential) | 60 |
| Decks | Same as area served |
| **Office** | |
| Office buildings | 50 |
| Lobbies and corridors above first floor | 80 |
| First floor corridors | 100 |
| Computer/data processing | 100 |
| **Assembly** | |
| Fixed seats (fastened to floor) | 60 |
| Movable seats | 100 |
| Stages and platforms | 125 |
| **Educational** | |
| Classrooms | 40 |
| Corridors above first floor | 80 |
| First floor corridors | 100 |
| **Retail** | |
| Retail floor area, first floor | 100 |
| Retail floor area, upper floors | 75 |
| Storage warehouse (light) | 125 |
| Storage warehouse (heavy) | 250 |
| **Healthcare** | |
| Operating rooms, laboratories | 60 |
| Patient rooms | 40 |
| Corridors above first floor | 80 |
| First floor corridors | 100 |
| **Industrial** | |
| Light manufacturing | 125 |
| Heavy manufacturing | 250 |
| **Parking** | |
| Passenger vehicles only | 40 |
| Trucks and buses | See code |
| **Stairs and Exits** | |
| Exit facilities serving A occ | 100 |
| All other stairs and exits | 100 |
| **Other** | |
| Roofs - Flat (occupiable) | 100 |
| Roofs - Flat (non-occupiable) | 20 |
| Roofs - Sloped | Per formula |
| Mechanical equipment areas | 125 |
| Libraries - Stack rooms | 150 |
| Libraries - Reading rooms | 60 |
| Gymnasiums | 100 |

### Concentrated Loads (Table 1607.1)

| Location | Concentrated Load (lbs) |
|----------|------------------------|
| Office floors | 2,000 |
| Retail floors | 1,000 |
| Garage (passenger) | 3,000 per wheel |
| Stair treads | 300 |
| Elevator machine room | 300 |
| Catwalks | 300 |
| Accessible roof | 300 |

---

## Dead Loads (1606)

### Typical Material Weights

| Material | Weight |
|----------|--------|
| **Concrete** | |
| Normal weight | 150 pcf |
| Lightweight | 110 pcf |
| Sand-lightweight | 120 pcf |
| **Masonry** | |
| CMU (grouted solid) | 140 pcf |
| CMU (ungrouted) | 85 pcf |
| Brick | 120 pcf |
| **Steel** | 490 pcf |
| **Wood** | |
| Southern pine | 37 pcf |
| Douglas fir | 34 pcf |
| Glulam/CLT | 32-36 pcf |
| **Glass** | 160 pcf |

### Typical Assembly Weights

| Assembly | Weight (psf) |
|----------|--------------|
| **Roofing** | |
| Built-up roofing | 6-7 |
| Single-ply membrane | 2-3 |
| Standing seam metal | 1-2 |
| Clay/concrete tile | 12-18 |
| Slate | 15-20 |
| Asphalt shingles | 3-4 |
| Green roof (extensive) | 15-35 |
| Green roof (intensive) | 50-150 |
| **Flooring** | |
| Concrete topping (1") | 12 |
| Hardwood (3/4") | 4 |
| Terrazzo (1") | 13 |
| Tile on mortar | 16 |
| Carpet + pad | 2 |
| Raised access floor | 5-8 |
| **Ceilings** | |
| Suspended acoustic tile | 2 |
| Gypsum board (5/8") | 3 |
| Metal pan | 3-5 |
| Plaster on lath | 8-10 |
| **Walls** | |
| Gypsum board (2 sides, steel stud) | 8-10 |
| CMU (8" grouted at 48") | 47 |
| CMU (8" ungrouted) | 35 |
| Glass curtain wall | 10-15 |
| Brick veneer | 40 |
| Stone veneer (4") | 55 |
| **Mechanical/Electrical** | |
| Allow for MEP | 5-10 |
| Heavy HVAC zones | 10-15 |

---

## Roof Live Loads (1607.12)

### Ordinary Flat Roofs (Non-Reducible Areas)

| Tributary Area | Live Load (psf) |
|----------------|-----------------|
| 0 - 200 sq ft | 20 |
| 201 - 600 sq ft | 16 |
| Over 600 sq ft | 12 |

### Sloped Roof Reduction
```
Lr = Lo × R1 × R2

Where:
Lo = Base roof live load (20 psf)
R1 = 1 for At ≤ 200 sf
    = 1.2 - 0.001×At for 200 < At < 600 sf
    = 0.6 for At ≥ 600 sf
R2 = 1 for F ≤ 4
    = 1.2 - 0.05×F for 4 < F < 12
    = 0.6 for F ≥ 12

At = Tributary area (sq ft)
F = Inches of rise per foot of horizontal distance
```

---

## Snow Loads (1608)

### Ground Snow Load (pg)
- Varies by geographic location
- Reference ASCE 7 Figure 7.2-1 or local jurisdiction
- Examples:
  - Miami, FL: 0 psf
  - New York City: 30 psf
  - Chicago: 25 psf
  - Denver: 30 psf
  - Minneapolis: 50 psf

### Flat Roof Snow Load
```
pf = 0.7 × Ce × Ct × Is × pg

Where:
Ce = Exposure factor (0.7 - 1.2)
Ct = Thermal factor (1.0 - 1.3)
Is = Importance factor (0.8 - 1.2)
pg = Ground snow load
```

### Minimum Values
- Flat roof: pf or pg × Is, whichever greater
- Low-slope (≤ 15°): 20 psf minimum in high snow regions

---

## Wind Loads (1609)

### Risk Categories (Table 1604.5)

| Category | Description | Wind Importance Factor |
|----------|-------------|----------------------|
| I | Low hazard (agricultural, temporary) | 0.87 |
| II | Standard occupancy | 1.0 |
| III | Substantial hazard (schools, >300 assembly) | 1.15 |
| IV | Essential facilities (hospitals, fire stations) | 1.15 |

### Basic Wind Speeds (Vult) - Selected Cities
*3-second gust at 33' above ground, Exposure C*

| Location | Risk II | Risk III/IV |
|----------|---------|-------------|
| Miami-Dade | 175 mph | 180 mph |
| Houston | 130 mph | 140 mph |
| New Orleans | 150 mph | 160 mph |
| New York City | 110 mph | 120 mph |
| Chicago | 105 mph | 115 mph |
| San Francisco | 95 mph | 105 mph |
| Los Angeles | 95 mph | 100 mph |

### Exposure Categories

| Category | Description |
|----------|-------------|
| B | Urban, suburban, wooded areas |
| C | Open terrain, scattered obstructions < 30' |
| D | Flat, unobstructed coastal areas |

### Components & Cladding
- Higher pressures than MWFRS
- Critical for windows, doors, roofing
- Pressure coefficients per ASCE 7 Chapter 30

---

## Seismic Loads (1613)

### Seismic Design Categories (SDC)

| Category | Description | Requirements |
|----------|-------------|--------------|
| A | Very low seismic | Minimum requirements |
| B | Low seismic | Basic requirements |
| C | Moderate seismic | Additional detailing |
| D | High seismic | Special detailing |
| E | High seismic near fault | Enhanced requirements |
| F | High seismic, essential facility | Most stringent |

### SDC Determination
Based on:
1. Site Class (A through F, based on soil)
2. Mapped spectral accelerations (Ss, S1)
3. Risk Category

### Site Classes

| Class | Description | Typical vs (ft/s) |
|-------|-------------|-------------------|
| A | Hard rock | > 5,000 |
| B | Rock | 2,500 - 5,000 |
| C | Very dense soil/soft rock | 1,200 - 2,500 |
| D | Stiff soil (default) | 600 - 1,200 |
| E | Soft clay soil | < 600 |
| F | Site-specific required | Liquefiable, etc. |

### Seismic Force-Resisting Systems (Common)

| System | R | Ω0 | Cd | Height Limit (SDC D) |
|--------|---|----|----|---------------------|
| Special moment frame (steel) | 8 | 3 | 5.5 | NL |
| Special moment frame (concrete) | 8 | 3 | 5.5 | NL |
| Ordinary moment frame (steel) | 3.5 | 3 | 3 | NP |
| Special concentric braced frame | 6 | 2 | 5 | 160' |
| Eccentrically braced frame | 8 | 2 | 4 | 160' |
| Special shear wall (concrete) | 5 | 2.5 | 5 | 160' |
| Special shear wall (wood) | 6.5 | 3 | 4 | 65' |
| Ordinary shear wall (wood) | 2 | 2.5 | 2 | 35' |

NL = No Limit, NP = Not Permitted

---

## Flood Loads (1612)

### Flood Design Classes (ASCE 24)

| Class | Description | Freeboard |
|-------|-------------|-----------|
| 1 | Low hazard | BFE |
| 2 | Standard occupancy | BFE + 1' |
| 3 | Substantial hazard | BFE + 1' |
| 4 | Essential facilities | BFE + 2' |

BFE = Base Flood Elevation

### Coastal A-Zone & V-Zone Requirements
- Elevated above BFE
- Breakaway walls below BFE
- Foundation design for scour
- Flood venting or flood-resistant enclosures

---

## Load Combinations (1605)

### LRFD (Strength Design)

| Combination | Formula |
|-------------|---------|
| 1 | 1.4D |
| 2 | 1.2D + 1.6L + 0.5(Lr or S or R) |
| 3 | 1.2D + 1.6(Lr or S or R) + (L or 0.5W) |
| 4 | 1.2D + 1.0W + L + 0.5(Lr or S or R) |
| 5 | 1.2D + 1.0E + L + 0.2S |
| 6 | 0.9D + 1.0W |
| 7 | 0.9D + 1.0E |

### ASD (Allowable Stress Design)

| Combination | Formula |
|-------------|---------|
| 1 | D |
| 2 | D + L |
| 3 | D + (Lr or S or R) |
| 4 | D + 0.75L + 0.75(Lr or S or R) |
| 5 | D + (0.6W or 0.7E) |
| 6 | D + 0.75L + 0.75(0.6W) + 0.75(Lr or S or R) |
| 7 | D + 0.75L + 0.75(0.7E) + 0.75S |
| 8 | 0.6D + 0.6W |
| 9 | 0.6D + 0.7E |

Where:
- D = Dead load
- L = Live load
- Lr = Roof live load
- S = Snow load
- R = Rain load
- W = Wind load
- E = Earthquake load

---

## Live Load Reduction (1607.10)

### Basic Reduction Formula
```
L = Lo × (0.25 + 15/√(KLL × AT))

Where:
L = Reduced live load (psf)
Lo = Unreduced live load (psf)
KLL = Live load element factor
AT = Tributary area (sq ft)
```

### KLL Values

| Element | KLL |
|---------|-----|
| Interior columns | 4 |
| Exterior columns without cantilever | 4 |
| Edge columns with cantilever | 3 |
| Corner columns with cantilever | 2 |
| Edge beams without cantilever | 2 |
| Interior beams | 2 |
| All other members | 1 |

### Limitations
- Maximum reduction: 50% (one floor), 60% (2+ floors)
- Minimum L: 0.50 × Lo (members supporting one floor)
- Minimum L: 0.40 × Lo (members supporting 2+ floors)
- No reduction for:
  - Assembly (L > 100 psf)
  - Parking garages
  - Areas where L > 100 psf
  - Heavy storage

---

## Special Inspections (1705)

### Required Special Inspections

| Construction Type | Inspection Required |
|-------------------|---------------------|
| **Concrete** | |
| Cast-in-place (structural) | Continuous during placement |
| Reinforcement | Prior to placement |
| Pre-stressed/post-tensioned | Stressing operations |
| **Steel** | |
| Welding (structural) | Per AWS D1.1 |
| High-strength bolting | Per RCSC Specification |
| **Masonry** | |
| Reinforced masonry | Grouting and reinforcement |
| Unreinforced masonry | Periodic mortar joints |
| **Wood** | |
| High-load diaphragms | Nailing, sheathing |
| Metal-plate trusses | Fabrication (QC) |
| **Soils** | |
| Verification of bearing | Continuous during earthwork |
| Fill placement | Periodic during compaction |
| Drilled shafts | Drilling and concrete |
| Driven piles | Driving and cutoff |
| **Seismic (SDC C and above)** | |
| Additional items per code | Per ASCE 7 requirements |

---

## Deflection Limits (Table 1604.3)

| Construction | Live Load | Dead + Live |
|--------------|-----------|-------------|
| Roof members (plaster ceiling) | L/360 | L/240 |
| Roof members (non-plaster) | L/180 | L/120 |
| Floor members | L/360 | L/240 |
| Exterior walls (wind) | - | H/240 |
| Interior partitions | - | L/240 |
| Farm buildings | L/180 | L/120 |
| Greenhouses | L/120 | L/60 |

L = Span length
H = Wall height

---

## Foundation Requirements (Chapter 18)

### Presumptive Bearing Capacities (Table 1806.2)

| Soil Type | Allowable Bearing (psf) |
|-----------|------------------------|
| Crystalline bedrock | 12,000 |
| Sedimentary rock | 4,000 |
| Sandy gravel (GW, GP) | 3,000 |
| Sand, silty sand (SW, SP) | 2,000 |
| Clay, sandy clay (CL, ML) | 1,500 |
| Soft clay, silt (CH, MH) | 1,000 |

### Minimum Footing Dimensions

| Building Type | Width | Depth Below Grade |
|---------------|-------|-------------------|
| 1-2 story conventional | 12" | 12" below undisturbed |
| 3 story conventional | 18" | 12" below undisturbed |
| All buildings | Per design | Below frost line |

### Frost Depth (Selected Locations)
- Florida: 0" (no frost protection required)
- Georgia: 6"
- Virginia: 18"
- New York: 36"
- Chicago: 42"
- Minneapolis: 48"

---

*Reference: IBC 2021 Chapter 16, ASCE 7-16*
*Always verify with local jurisdiction for amendments*

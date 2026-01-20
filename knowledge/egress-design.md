# Egress Design

## Fundamental Concepts

### Means of Egress Components
| Component | Definition |
|-----------|------------|
| Exit access | Path from any point to an exit |
| Exit | Protected path to exit discharge |
| Exit discharge | Path from exit to public way |

### Exit Types
| Type | Description |
|------|-------------|
| Exterior door | At grade to public way |
| Exit enclosure | Protected stairwell |
| Exit passageway | Protected horizontal exit |
| Horizontal exit | Through fire wall |
| Exterior exit stair | Open-air stairway |
| Exit ramp | Protected ramp |

---

## Occupant Load

### Occupant Load Factors
| Use | SF/Person |
|-----|-----------|
| Assembly (standing) | 5 |
| Assembly (chairs, no tables) | 7 |
| Assembly (tables and chairs) | 15 |
| Business | 100 |
| Educational (classroom) | 20 |
| Industrial | 100 |
| Institutional (sleeping) | 120 |
| Mercantile (basement/ground) | 30 |
| Mercantile (upper floors) | 60 |
| Residential | 200 |
| Storage | 300 |
| Parking garage | 200 |

### Calculating Occupant Load
```
Occupant Load = Floor Area / Occupant Load Factor

Example:
10,000 SF office / 100 SF per person = 100 occupants
```

### Multiple Uses
```
1. Calculate each use separately
2. Sum all occupant loads
3. Provide egress for total
```

---

## Number of Exits

### Minimum Exits Required
| Occupant Load | Exits |
|---------------|-------|
| 1-500 | 2 |
| 501-1,000 | 3 |
| > 1,000 | 4 |

### Single Exit Conditions (IBC)
| Occupancy | Max Occupants | Max Travel |
|-----------|---------------|------------|
| Business | 49 | 75' |
| Storage | 29 | 75' |
| Residential | 20 | 125' |
| Industrial | 49 | 75' |

### Stories with Single Exit (Sprinklered)
| Stories | Occupants | Travel |
|---------|-----------|--------|
| 1 | 49 | 100' |
| 2 | 30 | 75' |

---

## Exit Width

### Width Calculations
| System | Inches/Occupant |
|--------|-----------------|
| Stairs (sprinklered) | 0.2" |
| Stairs (unsprinklered) | 0.3" |
| Other (sprinklered) | 0.15" |
| Other (unsprinklered) | 0.2" |

### Minimum Widths
| Component | Minimum |
|-----------|---------|
| Door | 32" clear |
| Corridor | 44" |
| Stair | 44" |
| Aisle | 36" (varies) |
| Ramp | 44" |

### Example Calculation
```
500 occupants, sprinklered:
Stair width = 500 × 0.2" = 100" (two 50" stairs)
Door width = 500 × 0.15" = 75" (two 38" doors)
```

---

## Travel Distance

### Maximum Travel Distance
| Occupancy | Unsprinklered | Sprinklered |
|-----------|---------------|-------------|
| Business | 200' | 300' |
| Educational | 200' | 250' |
| Factory | 200' | 250' |
| Hazardous | 75' | 100' |
| Institutional | 150' | 200' |
| Mercantile | 200' | 250' |
| Residential | 200' | 250' |
| Storage | 200' | 400' |

### Common Path of Egress
| Occupancy | Unsprinklered | Sprinklered |
|-----------|---------------|-------------|
| Business | 75' | 100' |
| Mercantile | 75' | 100' |
| Factory/Industrial | 75' | 100' |
| Storage | 75' | 100' |

### Dead-End Corridors
| Condition | Maximum |
|-----------|---------|
| Unsprinklered | 20' |
| Sprinklered | 50' |

---

## Exit Access

### Corridor Requirements
| Feature | Requirement |
|---------|-------------|
| Width | 44" minimum |
| Height | 7'-6" minimum |
| Projection | 4" max below 80" |
| Rating | 1 hour (> 30 occupants) |
| Rating (sprinklered) | 0.5 hour (10-30 occ) |

### Door Swing
| Occupants | Swing Direction |
|-----------|-----------------|
| < 50 | Either direction |
| ≥ 50 | In direction of travel |
| Exit enclosure | In direction of travel |

### Door Hardware
| Feature | Requirement |
|---------|-------------|
| Operation | Single motion |
| Force (interior) | 5 lbs max |
| Force (fire door) | 30 lbs to release |
| Panic hardware | Required ≥ 100 occupants |

### Locking
| Type | Use |
|------|-----|
| Key-operated | From inside, code limits |
| Delayed egress | 15-30 sec delay, alarmed |
| Sensor-release | Special conditions |
| Access controlled | Fail-safe release |

---

## Exit Enclosures

### Fire Rating
| Building Height | Rating |
|-----------------|--------|
| 4 stories or less | 1 hour |
| More than 4 stories | 2 hours |

### Enclosure Requirements
| Feature | Requirement |
|---------|-------------|
| Construction | Fire-rated assembly |
| Opening protection | Rated doors |
| Penetrations | Limited, protected |
| Ventilation | Natural or pressurized |

### What's Allowed
| Allowed | Not Allowed |
|---------|-------------|
| Exit discharge corridor | Storage |
| Elevator lobby | Equipment |
| Exit passageway | Piping/ductwork (generally) |

---

## Stairs

### Dimensional Requirements
| Component | Residential | Commercial |
|-----------|-------------|------------|
| Riser (max) | 7-3/4" | 7" |
| Tread (min) | 10" | 11" |
| Width (min) | 36" | 44" |
| Headroom (min) | 6'-8" | 6'-8" |

### Landing Requirements
| Feature | Requirement |
|---------|-------------|
| Depth | Equal to stair width |
| Width | Equal to stair width |
| Max rise between | 12'-0" |

### Handrails
| Feature | Requirement |
|---------|-------------|
| Height | 34"-38" |
| Extension (top) | 12" horizontal |
| Extension (bottom) | Tread depth + 12" |
| Graspability | 1-1/4" to 2" diameter |
| Continuity | Full length of flight |

---

## Ramps

### Slope Requirements
| Application | Max Slope |
|-------------|-----------|
| Accessible route | 1:12 (8.33%) |
| Curb ramp | 1:12 |
| Existing buildings | 1:10 (with limits) |
| Egress (non-accessible) | 1:8 (12.5%) |

### Dimensions
| Feature | Requirement |
|---------|-------------|
| Width | 44" minimum |
| Rise per run | 30" maximum |
| Landing length | 60" minimum |
| Landing width | Width of ramp |

### Handrails
| Feature | Requirement |
|---------|-------------|
| Required | Both sides if rise > 6" |
| Height | 34"-38" |
| Extensions | 12" at top and bottom |

---

## Assembly Seating

### Aisle Width
| Aisle Type | Minimum Width |
|------------|---------------|
| Level (no seats) | 36" |
| Level (with seats) | 42" |
| Ramped (< 1:8) | 36" at row |
| Stepped (at row) | 22" + 0.005"/seat |

### Row Spacing
| Rows to Aisle | Clear Width |
|---------------|-------------|
| 7 or less | 12" min |
| 8-14 | 12" + 0.3" per seat |
| 15+ | 12" + 0.6" per seat |

### Aisle Accessways
| Feature | Requirement |
|---------|-------------|
| Min clear | 12" |
| Max seats to aisle | 7 (without continental) |
| Continental | 100 seats max per row |

---

## Special Conditions

### High-Rise (> 75')
| Feature | Requirement |
|---------|-------------|
| Stair pressurization | Required |
| Firefighter elevator | Required |
| Voice alarm | Required |
| Standby power | Egress lighting |
| Area of refuge | At elevators |

### Assembly
| Feature | Requirement |
|---------|-------------|
| Main exit | 50% of egress capacity |
| Other exits | Distributed |
| Panic hardware | ≥ 100 occupants |
| Crowd management | > 6,000 occupants |

### Healthcare
| Feature | Requirement |
|---------|-------------|
| Defend in place | Primary strategy |
| Smoke compartments | 22,500 SF max |
| Corridor width | 8'-0" (patient transport) |
| Ramps | Required for gurneys |

---

## Emergency Lighting

### Requirements
| Duration | 90 minutes minimum |
| Level | 1 FC average initially |
| Level (end) | 0.6 FC average |
| Ratio | 40:1 max/min |

### Locations Required
| Area |
|------|
| Exit access corridors |
| Exit enclosures |
| Exit discharge |
| Assembly seating |
| Electrical rooms |

---

## Exit Signs

### Illumination
| Type | Requirement |
|------|-------------|
| Internal | 5 FC on face |
| External | 5 FC on face |
| Self-luminous | 0.06 FL |
| Battery backup | 90 minutes |

### Placement
| Location | Requirement |
|----------|-------------|
| At exits | Required |
| Path to exit | Visible from any point |
| Direction | Arrows where needed |
| Height | 80" AFF to bottom |
| Ceiling | Per code |

### Visibility
| Condition | Distance |
|-----------|----------|
| Internally lit | 100' max |
| Externally lit | 100' max |
| Floor-level | 18" AFF, 200' spacing |

---

## Areas of Refuge

### When Required
| Condition | Required |
|-----------|----------|
| Unsprinklered buildings | Yes |
| Sprinklered buildings | No (usually) |
| High-rise | At elevator |
| Elevator lobby | Smokeproof |

### Size
| Feature | Requirement |
|---------|-------------|
| Space per wheelchair | 30" × 48" |
| Location | Within exit enclosure |
| Communication | Two-way to fire command |

### Signage
| Sign | Location |
|------|----------|
| International symbol | At refuge |
| Directional | On path to refuge |

---

## Checklists

### Egress Plan Review
- [ ] Occupant loads calculated
- [ ] Number of exits adequate
- [ ] Exit separation (1/3 diagonal)
- [ ] Travel distance verified
- [ ] Common path verified
- [ ] Dead ends verified
- [ ] Exit widths calculated
- [ ] Stair capacity verified
- [ ] Door swings correct
- [ ] Hardware compliant
- [ ] Exit enclosures rated
- [ ] Emergency lighting shown
- [ ] Exit signs shown

### Field Verification
- [ ] Doors operate correctly
- [ ] Exit path unobstructed
- [ ] Signs visible and lit
- [ ] Emergency lights functional
- [ ] Panic hardware operable
- [ ] Self-closing doors close
- [ ] Corridor width maintained

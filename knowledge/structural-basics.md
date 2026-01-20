# Structural Basics for Architects

## Load Path Fundamentals

### Gravity Load Path
```
Roof loads → Roof framing → Headers/beams → Columns/studs →
Foundation walls → Footings → Soil
```

### Lateral Load Path (Wind/Seismic)
```
Wind on wall → Diaphragm (roof/floor) → Shear walls →
Foundation → Soil
```

### Key Principle
**Loads must have continuous path to ground.** Every beam needs support. Every column needs footing.

---

## Span Tables Quick Reference

### Wood Floor Joists (40 psf live load)
| Size | 12" O.C. | 16" O.C. | 24" O.C. |
|------|----------|----------|----------|
| 2x8 | 13'-1" | 11'-10" | 9'-8" |
| 2x10 | 16'-5" | 14'-11" | 12'-4" |
| 2x12 | 19'-1" | 17'-4" | 14'-4" |

### Wood Rafters (20 psf live load)
| Size | 12" O.C. | 16" O.C. | 24" O.C. |
|------|----------|----------|----------|
| 2x6 | 13'-6" | 12'-4" | 10'-1" |
| 2x8 | 17'-10" | 16'-2" | 13'-4" |
| 2x10 | 22'-5" | 20'-4" | 16'-9" |

### Wood Headers (Exterior Bearing Wall)
| Opening | Header Size |
|---------|-------------|
| Up to 4' | 2-2x6 or 4x6 |
| 4' to 6' | 2-2x8 or 4x8 |
| 6' to 8' | 2-2x10 or 4x10 |
| 8' to 10' | 2-2x12 or 4x12 |
| Over 10' | Engineer required |

### Steel Beam Rules of Thumb
| Span | Depth (residential) |
|------|---------------------|
| 10' | W8 |
| 15' | W10 |
| 20' | W12 |
| 25' | W14 |
| 30'+ | W16+ (engineer) |

---

## Common Structural Systems

### Residential
| System | Spans | Best For |
|--------|-------|----------|
| Wood stud bearing | Up to 12' between supports | Single-family homes |
| Wood truss roof | Up to 40' clear span | Typical residential |
| Wood I-joist floor | Up to 30' | Long spans, open plans |
| Steel beam + wood | Unlimited | Open floor plans |

### Commercial
| System | Spans | Best For |
|--------|-------|----------|
| Steel frame | 30'-60' typical | Offices, retail |
| Concrete frame | 25'-35' typical | Multi-story, parking |
| Bar joist + deck | 30'-50' | Single-story commercial |
| Pre-engineered metal | 60'-100'+ | Warehouses, industrial |
| Wood heavy timber | 30'-50' | Exposed structure aesthetic |

### Multi-Family
| System | Heights | Best For |
|--------|---------|----------|
| Wood frame (Type V) | Up to 4 stories | Garden apartments |
| Wood over podium | 5-6 stories total | Urban mid-rise |
| Concrete/steel | 7+ stories | High-rise |

---

## Column and Footing Sizing

### Wood Post Capacity (rough)
| Size | Capacity (8' height) |
|------|----------------------|
| 4x4 | 8,000 lbs |
| 4x6 | 12,000 lbs |
| 6x6 | 20,000 lbs |

### Steel Column Capacity (rough)
| Size | Capacity (10' height) |
|------|----------------------|
| HSS 4x4x1/4 | 50 kips |
| HSS 6x6x1/4 | 100 kips |
| W8x31 | 200 kips |

### Footing Sizing Rule of Thumb
```
Footing area = Load / Soil bearing capacity

Example:
- Column load: 20,000 lbs
- Soil capacity: 2,000 psf
- Footing area: 20,000 / 2,000 = 10 SF
- Footing size: 3'-6" x 3'-6" (or round to 4'x4')
```

### Continuous Footing Width
| Load | Width (2000 psf soil) |
|------|-----------------------|
| 1-story wood | 12" |
| 2-story wood | 16" |
| 1-story masonry | 16" |
| 2-story masonry | 20" |

---

## Openings in Structural Elements

### Wall Openings
- Headers required over all openings in bearing walls
- Non-bearing walls: no header, but still need support for wall above
- Jack studs (trimmers) support header ends
- King studs support jack studs

### Floor Openings
- Openings > 4" require framing
- Use double headers and trimmers
- Joist hangers at all connections
- Opening > 6' in either direction: engineer required

### Beam Penetrations
**Generally avoid.** If required:
- Middle third of span only
- Max diameter = 1/3 beam depth
- Maintain 2" to top and bottom edges
- Never at supports or high shear areas

---

## Shear Walls and Bracing

### Shear Wall Requirements
| Building Height | Min Wall Length |
|-----------------|-----------------|
| 1 story | 25% of building length |
| 2 story | 40% of building length |
| 3 story | 50% of building length |

### Shear Wall Construction
```
Components:
- Structural sheathing (plywood/OSB)
- Specific nailing pattern (edge and field)
- Hold-downs at ends
- Anchor bolts to foundation
- Continuous from roof to foundation
```

### Braced Wall Panels (Residential)
| Method | Sheathing | Nailing |
|--------|-----------|---------|
| WSP (wood structural panel) | 7/16" OSB min | 6" edge, 12" field |
| WSP w/ hold-downs | 7/16" OSB min | 4" edge, 12" field |
| Let-in bracing | 1x4 diagonal | 2 nails each stud |

---

## Connection Types

### Wood Connections
| Connection | Hardware |
|------------|----------|
| Joist to beam | Joist hanger |
| Beam to post | Post cap |
| Post to beam | Post base |
| Rafter to plate | Hurricane tie |
| Header to king stud | Hanger or nails |
| Sill to foundation | Anchor bolt |

### Steel Connections
| Connection | Type |
|------------|------|
| Beam to column | Shear tab, moment frame |
| Column to base | Base plate + anchor bolts |
| Beam to beam | Bolted or welded |
| Bracing | Gusset plates |

### Connection Capacity (Simpson Strong-Tie examples)
| Product | Capacity |
|---------|----------|
| LUS26 (2x6 hanger) | 1,185 lbs |
| LUS210 (2x10 hanger) | 2,360 lbs |
| H1 hurricane tie | 585 lbs uplift |
| HD5A hold-down | 4,565 lbs |
| MASA mudsill anchor | 1,605 lbs shear |

---

## Deflection Limits

### Standard Deflection Limits
| Element | Live Load | Total Load |
|---------|-----------|------------|
| Floor (plastered ceiling) | L/360 | L/240 |
| Floor (no plaster) | L/240 | L/180 |
| Roof (plastered ceiling) | L/360 | L/240 |
| Roof (no plaster) | L/180 | L/120 |

### Deflection Calculation
```
Max deflection = Span / Limit

Example:
- 20' floor span with plaster
- Limit: L/360
- Max deflection: 240" / 360 = 0.67" (about 5/8")
```

---

## When to Involve Structural Engineer

### Always Required
- Buildings over 3 stories
- Clear spans over 40'
- Unusual loading conditions
- Seismic design categories D, E, F
- Post-tensioned concrete
- Moment frames
- Retaining walls over 4'
- Basement walls with surcharge

### Typically Required
- Open floor plans with long spans
- Removing bearing walls
- Large openings in shear walls
- Heavy equipment (rooftop HVAC)
- Pool or spa on structure
- Cantilevers over 4'

### Architect Can Design (Per Code)
- Conventional light-frame construction
- One and two-family dwellings (with prescriptive tables)
- Simple additions following original construction
- Non-structural elements

---

## Florida/Hurricane Considerations

### Wind Speed Design
| Location | Design Wind Speed |
|----------|-------------------|
| Inland Florida | 130-140 mph |
| Coastal Florida | 150-170 mph |
| Miami-Dade HVHZ | 180+ mph |

### Hurricane Strapping Requirements
- Every rafter/truss to wall
- Wall to floor at each level
- Continuous strap or threaded rod for uplift
- Hold-downs at shear wall ends

### Impact Protection
- Glazing within 30' of grade
- All openings in HVHZ
- Garage doors rated for wind zone

### Roof-to-Wall Connection
```
Load path for uplift:
Roof sheathing → Rafters/trusses (H-clips) →
Hurricane straps → Top plate → Studs →
Straps/anchor bolts → Foundation
```

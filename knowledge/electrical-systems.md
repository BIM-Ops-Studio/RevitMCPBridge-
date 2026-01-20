# Electrical Systems Design

## Service and Distribution

### Service Sizing
| Building Type | VA/SF |
|---------------|-------|
| Residential | 3-5 |
| Office | 5-10 |
| Retail | 3-8 |
| Restaurant | 10-20 |
| Healthcare | 15-25 |
| Industrial | 10-30 |
| Data center | 100-300 |

### Service Entrance
| Service Size | Wire Size | Conduit |
|--------------|-----------|---------|
| 100A | #4 Cu / #2 Al | 1-1/4" |
| 200A | 2/0 Cu / 4/0 Al | 2" |
| 400A | 400 kcmil | 3" |
| 600A | 2×350 kcmil | 2×3" |
| 800A | 2×500 kcmil | 2×3-1/2" |

### Panel Sizing
| Circuits | Panel Size |
|----------|------------|
| 12-20 | 100A |
| 24-30 | 125-150A |
| 30-42 | 200A |
| 42+ | 225A+ |

### Voltage Systems
| System | Use |
|--------|-----|
| 120/240V 1φ | Residential |
| 120/208V 3φ | Commercial |
| 277/480V 3φ | Large commercial |
| 480V 3φ | Industrial, motors |

---

## Branch Circuits

### Circuit Sizing
| Load Type | Wire Size | Breaker |
|-----------|-----------|---------|
| General outlets | #12 AWG | 20A |
| Lighting | #12 or #14 | 15-20A |
| Kitchen appliance | #12 AWG | 20A |
| Refrigerator | #12 AWG | 20A |
| Dishwasher | #12 AWG | 20A |
| Disposal | #12 AWG | 20A |
| Microwave | #12 AWG | 20A |
| Washer | #12 AWG | 20A |
| Dryer (electric) | #10 AWG | 30A |
| Range (electric) | #6 AWG | 50A |
| Water heater | #10 AWG | 30A |
| HVAC (small) | #10 AWG | 30A |
| HVAC (large) | Per nameplate | Per nameplate |

### Outlet Spacing
| Location | Requirement |
|----------|-------------|
| Residential wall | 6' max from any point |
| Kitchen counter | 24" max between |
| Bathroom | 1 per sink |
| Garage | 1 per car space |
| Outdoor | Front and back |
| Commercial | Per design |

### Dedicated Circuits
| Appliance | Dedicated |
|-----------|-----------|
| Refrigerator | Yes |
| Dishwasher | Yes |
| Disposal | Yes (can share) |
| Microwave | Yes |
| Range/oven | Yes |
| Dryer | Yes |
| Washer | Yes |
| Water heater | Yes |
| Furnace | Yes |
| AC condenser | Yes |

---

## Lighting

### Light Levels (Foot-candles)
| Space | FC Required |
|-------|-------------|
| Parking | 1-5 |
| Corridor | 10-20 |
| Lobby | 10-30 |
| Office (general) | 30-50 |
| Office (task) | 50-75 |
| Classroom | 50-75 |
| Conference | 30-50 |
| Retail (general) | 50-75 |
| Retail (feature) | 100-200 |
| Industrial | 30-100 |
| Warehouse | 10-30 |
| Healthcare (exam) | 50-100 |
| Healthcare (OR) | 2,000+ |

### Lighting Power Density (LPD)
| Building Type | W/SF (Code Max) |
|---------------|-----------------|
| Office | 0.82-0.98 |
| Retail | 1.06-1.40 |
| Healthcare | 0.96-1.21 |
| Warehouse | 0.45-0.66 |
| School | 0.87-0.99 |
| Hotel | 0.75-0.91 |

### Lamp Types
| Type | Efficacy (lm/W) | Life (hours) |
|------|-----------------|--------------|
| Incandescent | 10-18 | 1,000 |
| Halogen | 15-25 | 2,000-4,000 |
| Fluorescent | 50-100 | 20,000-30,000 |
| LED | 80-200 | 50,000-100,000 |
| HID (metal halide) | 75-100 | 10,000-20,000 |

### Emergency Lighting
| Requirement | Duration |
|-------------|----------|
| Exit signs | 90 minutes |
| Egress paths | 90 minutes |
| Minimum level | 1 FC average |
| Battery backup | Required |
| Generator | For essential |

---

## Motors and Equipment

### Motor Starting
| Method | Use |
|--------|-----|
| Across-the-line | Small motors (< 5 HP) |
| Soft start | Medium motors |
| VFD | Variable speed |
| Star-delta | Large motors |
| Autotransformer | Large motors |

### Motor Protection
| Protection | Purpose |
|------------|---------|
| Overload | Thermal protection |
| Short circuit | Fuses/breaker |
| Ground fault | GFPE |
| Phase loss | Monitor |
| Undervoltage | Contactor |

### Conductor Sizing for Motors
| Motor HP (3φ) | Wire Size | Breaker |
|---------------|-----------|---------|
| 1/2 | #14 | 15A |
| 1 | #14 | 15A |
| 2 | #12 | 20A |
| 3 | #10 | 30A |
| 5 | #8 | 40A |
| 7.5 | #6 | 50A |
| 10 | #6 | 60A |
| 15 | #4 | 80A |
| 20 | #3 | 100A |
| 25 | #1 | 110A |

---

## Grounding and Bonding

### Grounding Requirements
| System | Electrode |
|--------|-----------|
| Residential | 2 rods, 8' each, 6' apart |
| Commercial | Concrete-encased (Ufer) |
| Supplemental | Water pipe (first 5') |
| Building steel | If available |

### Equipment Grounding
| Circuit Size | EGC Size |
|--------------|----------|
| 15-20A | #14 Cu |
| 30A | #10 Cu |
| 40-60A | #10 Cu |
| 100A | #8 Cu |
| 200A | #6 Cu |
| 400A | #3 Cu |

### Bonding
| Item | Required |
|------|----------|
| Water pipe | Yes |
| Gas pipe | Yes |
| Telecom | Yes |
| CSST | Yes (special) |
| Metal enclosures | Yes |

---

## Special Systems

### Fire Alarm
| Component | Function |
|-----------|----------|
| FACP | Control panel |
| Smoke detector | Detection |
| Heat detector | Detection |
| Pull station | Manual alarm |
| Horn/strobe | Notification |
| NAC | Notification circuit |

### Fire Alarm Spacing
| Device | Spacing |
|--------|---------|
| Smoke (spot) | 30' typical |
| Heat (spot) | 50' typical |
| Beam detector | 60' typical |
| Duct detector | Per duct |

### Generator Systems
| Load | Generator Size |
|------|----------------|
| Life safety | Emergency loads only |
| Legally required | Code-mandated |
| Optional standby | Owner preference |
| Prime power | Continuous |

### UPS Systems
| Type | Use |
|------|-----|
| Offline | Basic protection |
| Line-interactive | Office equipment |
| Online | Critical loads |
| Rotary | Large facilities |

---

## Low Voltage Systems

### Categories
| System | Voltage |
|--------|---------|
| Data/voice | Cat6/6A |
| Security | 12-24V DC |
| Fire alarm | 24V DC |
| AV | Varies |
| Access control | 12-24V DC |
| Nurse call | 24V DC |

### Data Cabling
| Category | Speed | Distance |
|----------|-------|----------|
| Cat5e | 1 Gbps | 100m |
| Cat6 | 10 Gbps | 55m |
| Cat6A | 10 Gbps | 100m |
| Cat8 | 40 Gbps | 30m |
| Fiber (MM) | 10+ Gbps | 300-550m |
| Fiber (SM) | 10+ Gbps | 10+ km |

### Telecom Rooms
| Size | Closet Size |
|------|-------------|
| 5,000 SF | 8' × 8' |
| 10,000 SF | 10' × 10' |
| 20,000 SF | 12' × 12' |
| Per floor | 1 per 10,000 SF |

---

## Energy Efficiency

### Lighting Controls
| Control | Savings |
|---------|---------|
| Occupancy sensors | 20-40% |
| Daylight harvesting | 15-35% |
| Scheduling | 10-20% |
| Personal dimming | 10-20% |
| Tunable white | 5-15% |

### Motor Efficiency
| Efficiency Level | Premium |
|------------------|---------|
| Standard | 0% |
| High efficiency | 2-5% better |
| Premium efficiency | 5-10% better |
| VFD controlled | 20-50% better |

### Power Factor Correction
| PF | Action |
|----|--------|
| > 0.95 | None needed |
| 0.85-0.95 | Consider correction |
| < 0.85 | Correction required |

---

## Code Requirements

### GFCI Locations
| Location | Required |
|----------|----------|
| Bathroom | All outlets |
| Kitchen counter | Within 6' of sink |
| Garage | All outlets |
| Outdoors | All outlets |
| Basement (unfinished) | All outlets |
| Crawl space | All outlets |
| Laundry | Sink area |
| Pool/spa | Within 20' |

### AFCI Requirements
| Location | Required |
|----------|----------|
| Bedrooms | Yes |
| Living areas | Yes |
| Dining rooms | Yes |
| Family rooms | Yes |
| Hallways | Yes |
| Closets | Yes |
| Kitchens | Yes |
| Laundry | Yes |

### Tamper-Resistant Outlets
| Location | Required |
|----------|----------|
| All residential | Yes |
| Child care | Yes |
| Healthcare | Yes |
| Common areas | Yes |

---

## Accessibility

### Outlet Heights
| Location | Height |
|----------|--------|
| Standard | 15"-48" AFF |
| ADA accessible | 15"-48" AFF |
| Countertop | Above counter |
| Floor | Allowed if accessible |

### Switch Heights
| Location | Height |
|----------|--------|
| Standard | 48" max AFF |
| ADA | 48" max AFF |
| Above counter | 48" max from floor |

### Controls
| Feature | Requirement |
|---------|-------------|
| Operation | One hand, no grasp |
| Force | 5 lbs max |
| Signage | Braille on panels |

---

## Metering

### Metering Types
| Type | Use |
|------|-----|
| Master meter | Single owner |
| Individual | Multi-tenant |
| Submetering | Tenant billing |
| Check meter | Verification |

### Meter Location
| Requirement | Dimension |
|-------------|-----------|
| Height | 5'-6" typical |
| Clearance | 36" front |
| Access | Utility readable |
| Weather protection | NEMA 3R |

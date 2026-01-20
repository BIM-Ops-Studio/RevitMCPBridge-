# Florida Building Code - MEP Requirements

**Based on**: 7th Edition Florida Building Code (2023)
**Applicable Codes**: FBC Mechanical, FBC Fuel Gas, Florida Energy Conservation Code (FECC)

---

## Quick Reference - Critical Values

| Requirement | Value | Code Reference |
|-------------|-------|----------------|
| Min outdoor air (office) | 5 CFM/person + 0.06 CFM/sf | FECC Table 403.3.1.1 |
| Max duct leakage (new) | 4 CFM/100 sf @25 Pa | FECC 403.3.5 |
| Min exhaust - bathroom | 50 CFM intermittent / 20 CFM continuous | FBC-M 403.3.1 |
| Min exhaust - kitchen (residential) | 100 CFM intermittent / 25 CFM continuous | FBC-M 403.3.1 |
| Min exhaust - kitchen (commercial) | 300-600 CFM per linear foot hood | FBC-M 507.2 |
| Equipment clearance (gas) | Per manufacturer / 18" combustible | FBC-M 306 |
| Condensate drain pipe | 3/4" min ID | FBC-M 307.2.3 |
| Refrigerant piping insulation | 1/2" - 1" based on size | FECC Table 403.2.10 |
| Service panel clearance | 30"W × 36"D × 78"H | NEC 110.26 |
| GFCI - bathrooms | All receptacles | NEC 210.8(A)(1) |
| GFCI - kitchens | All countertop receptacles | NEC 210.8(A)(6) |
| AFCI - bedrooms | All outlets | NEC 210.12 |

---

## HVAC Systems (FBC Mechanical)

### Ventilation Requirements (Chapter 4)

#### Natural Ventilation (401)
- **Opening area**: 4% of floor area minimum
- **Location**: Openings to outdoor air or approved ventilating court
- **Rooms without exterior**: Mechanical ventilation required

#### Mechanical Ventilation (403)
Outdoor air requirements per ASHRAE 62.1 / FECC:

| Occupancy | CFM/Person | CFM/sq ft |
|-----------|------------|-----------|
| **Office** | 5 | 0.06 |
| **Conference room** | 5 | 0.06 |
| **Retail (mall common)** | 7.5 | 0.06 |
| **Restaurant dining** | 7.5 | 0.18 |
| **Classroom (age 5+)** | 10 | 0.12 |
| **Hotel/motel bedroom** | 5 | 0.06 |
| **Lobby (hotel)** | 7.5 | 0.06 |
| **Healthcare exam room** | 5 | 0.06 |
| **Healthcare patient room** | 25 | - |
| **Gym/Exercise room** | 20 | 0.06 |

#### Exhaust Requirements (403.3)

| Space | Exhaust Rate (CFM/sf) | Notes |
|-------|----------------------|-------|
| Toilet rooms (public) | 50/fixture (intermittent) | Or 25 CFM/fixture continuous |
| Toilet rooms (private) | 50 (intermittent) | Or 20 CFM continuous |
| Shower rooms | 50/stall | Ducted to exterior |
| Kitchen (residential) | 100 (intermittent) | Or 25 CFM continuous |
| Kitchen (commercial) | Per hood design | Type I/II hoods |
| Locker rooms | 0.5 | 25 CFM/locker min |
| Smoking lounges | 60 | Dedicated exhaust |
| Janitor closets | 1.0 | Exhausted to exterior |
| Parking garages | 0.75 | CO/NO2 sensors can reduce |
| Copy/print rooms | 0.5 | - |
| Nail salons | 0.6 | Special air handling |

### Commercial Kitchen Hoods (Chapter 5)

#### Type I Hoods (Grease-Laden Vapors)
Required over:
- Commercial cooking equipment
- High-temperature dishwashers
- Equipment producing grease vapors

**Exhaust rates (FBC-M 507.2.1)**:

| Hood Type | CFM per Linear Foot |
|-----------|---------------------|
| Wall-mounted canopy | 300-500 |
| Island canopy | 400-600 |
| Single island (back-to-back) | 300-500 per side |
| Proximity (low profile) | 250-450 |
| Eyebrow | 250-400 |

**Fire suppression**: Required for Type I hoods (NFPA 17A, 96)

#### Type II Hoods (Heat/Steam/Odors)
Required over:
- Dishwashers (non-high-temp)
- Ovens not producing grease
- Steam equipment

**Exhaust rates**: 150-300 CFM/linear foot

### Duct Systems (Chapter 6)

#### Duct Construction
| Material | Use | Thickness |
|----------|-----|-----------|
| Galvanized steel | Supply/return | 26-22 gauge |
| Aluminum | Supply/return | 0.016" - 0.032" |
| Flexible duct | Runouts only | Max 5' typical |
| Fiberglass duct board | Supply/return | R-4 to R-8 |

#### Duct Insulation (Florida Energy Code)
| Location | Minimum R-Value |
|----------|-----------------|
| Supply - unconditioned space | R-6 |
| Supply - exterior | R-8 |
| Return - unconditioned space | R-6 |
| Exhaust - through conditioned | R-4 |

#### Duct Sealing (FECC 403.3.5)
- **Sealed ducts**: All connections, joints, seams
- **Mastic or approved tape**: UL 181A-M/P, 181B-M/FX
- **Maximum leakage**: 4 CFM/100 sf @25 Pa (new construction)

### Equipment Installation (Chapter 3)

#### Clearances
| Equipment | Clearance | Notes |
|-----------|-----------|-------|
| Air handling units | Per manufacturer | Service access |
| Furnaces (gas) | 18" to combustible | Or per listing |
| Condensing units | 24" min one side | 36" service side |
| Kitchen exhaust fans | 18" to combustible | Or listed |

#### Condensate Drainage (307.2)
- **Drain line**: 3/4" ID minimum
- **Trap required**: On positive pressure side
- **Air gap**: 2× pipe diameter to drain
- **Secondary drain or float switch**: Required in ceiling spaces
- **Slope**: 1/8" per foot minimum

#### Hurricane Strapping
- **All rooftop equipment**: Must be strapped to structure
- **HVHZ**: Enhanced fastening per FBC High Velocity Zone
- **Product approval**: Required for rooftop installations

---

## Electrical Systems (NEC/NFPA 70)

### Service and Panels

#### Service Size (Residential)
| House Size | Minimum Service |
|------------|-----------------|
| < 2,500 sf | 200A |
| 2,500 - 4,000 sf | 200A - 400A |
| > 4,000 sf | 400A+ |
| Pool/spa | Add 50-60A subpanel |

#### Panel Location
- **Clearance**: 30" wide × 36" deep × 78" high (NEC 110.26)
- **Not permitted in**: Bathrooms, clothes closets, over stairs
- **Working space**: Clear, unobstructed, level floor
- **Illumination**: Dedicated light required

### Branch Circuits (Residential)

#### Required Circuits
| Circuit | Size | Quantity |
|---------|------|----------|
| Kitchen countertop | 20A GFCI | 2 minimum |
| Refrigerator | 20A | 1 dedicated |
| Dishwasher | 20A | 1 dedicated |
| Garbage disposal | 20A | May share with DW |
| Microwave | 20A | 1 dedicated |
| Bathroom | 20A GFCI | 1 per bath or shared |
| Laundry | 20A | 1 dedicated |
| Garage | 20A GFCI | 1 minimum |
| Outdoor | 20A GFCI | 1 front, 1 rear |
| HVAC | Per equipment | Dedicated |
| Water heater (electric) | 30A 240V | Dedicated |
| Electric range | 50A 240V | Dedicated |
| Electric dryer | 30A 240V | Dedicated |

#### General Lighting
- **15A or 20A circuits**: 600 sf per 15A, 800 sf per 20A
- **Every room**: At least one switched light outlet
- **Hallways/stairs**: Switched at each end

### GFCI Protection (NEC 210.8)

#### Residential GFCI Locations
- ✅ All bathroom receptacles
- ✅ Kitchen countertop receptacles (within 6' of sink)
- ✅ All garage receptacles
- ✅ Outdoor receptacles
- ✅ Crawl space (at or below grade)
- ✅ Unfinished basement
- ✅ Within 6' of sinks (laundry, wet bar)
- ✅ Boat houses
- ✅ Pool/spa areas

#### Commercial GFCI Locations
- ✅ Bathrooms
- ✅ Rooftops
- ✅ Kitchens (within 6' of sink)
- ✅ Outdoors
- ✅ Garages/service bays
- ✅ Indoor wet locations
- ✅ Locker rooms with showers

### AFCI Protection (NEC 210.12)

Required in (residential):
- ✅ All bedrooms
- ✅ Living rooms
- ✅ Dining rooms
- ✅ Family rooms
- ✅ Parlors
- ✅ Libraries
- ✅ Dens
- ✅ Sunrooms
- ✅ Recreation rooms
- ✅ Closets
- ✅ Hallways
- ✅ Laundry areas

**Note**: AFCI or combination AFCI/GFCI may be required

### Receptacle Spacing

#### Residential (NEC 210.52)
- **Wall space**: Every 12' of wall or fraction
- **Behind doors**: 6' from door to nearest outlet
- **Countertops**: Every 4' (2' from corners)
- **Islands**: 1 per 9 sq ft counter (first), additional per 18 sq ft
- **Peninsulas**: Same as islands

#### Hallways
- **10' or longer**: At least one receptacle

### Lighting Requirements

#### Required Lighting
| Location | Requirement |
|----------|-------------|
| Habitable rooms | Wall switch at entry |
| Bathroom | Wall switch at entry |
| Hallway | Switch at each end if >10' |
| Stairway | 3-way at top and bottom |
| Garage | Wall switch controlled |
| Outdoor entrances | Switch controlled |
| Attic/Crawl space | Switch at entry point |
| Storage/utility | Wall switch at entry |

#### Emergency Egress (Commercial)
- **Exit signs**: Illuminated, battery backup
- **Egress lighting**: 1 fc average, 90-minute battery
- **Monthly testing**: Required for emergency lighting

### Swimming Pools (NEC 680)

#### Clearances
| Item | Minimum Distance |
|------|------------------|
| Receptacles to pool edge | 6' (10' in FL) |
| Light fixtures (existing) to pool | 5' horizontal |
| Light fixtures (new) to pool | 12' unless 12' above water |
| Service equipment to pool | 5' |
| Overhead lines to pool | 22.5' (insulated), 25' (uninsulated) |

#### Bonding Required
- Pool shell (conductive)
- Metal ladder, rails
- Pool equipment
- Fence posts (metal)
- Pool cover mechanisms
- Nearby metal items (within 5')

#### GFCI/Equipment
- **Pool pump**: GFCI protected
- **Pool lights**: 12V or GFCI protected
- **Receptacles within 20'**: GFCI protected

---

## Florida Energy Conservation Code (FECC)

### Climate Zone
- **Florida**: All Climate Zone 2A (Hot-Humid)
- **Some South Florida**: Climate Zone 1 applies

### Equipment Efficiency

#### HVAC Minimums (Residential)
| System Type | Minimum Efficiency |
|-------------|-------------------|
| Split A/C | 15 SEER2 / 11.7 EER2 |
| Package A/C | 14 SEER2 / 11.2 EER2 |
| Heat pump (cooling) | 15 SEER2 / 11.7 EER2 |
| Heat pump (heating) | 8.1 HSPF2 |
| Gas furnace | 80% AFUE |

#### HVAC Minimums (Commercial)
Per ASHRAE 90.1-2019 or FECC Chapter 4

| Equipment | Size | Efficiency |
|-----------|------|------------|
| Packaged A/C | < 65 kBtu/h | 14.0 SEER |
| Packaged A/C | 65-135 kBtu/h | 11.2 EER |
| Packaged A/C | 135-240 kBtu/h | 11.0 EER |
| Packaged A/C | > 240 kBtu/h | 10.0 EER |
| Chillers (screw) | All | 0.75 kW/ton |
| Chillers (centrifugal) | All | 0.56 kW/ton |

#### Water Heating (Residential)
| Type | Minimum Efficiency |
|------|-------------------|
| Electric storage (30-55 gal) | 0.93 UEF |
| Electric storage (>55 gal) | 2.20 UEF (heat pump) |
| Gas storage (≤55 gal) | 0.64 UEF |
| Gas tankless | 0.87 UEF |
| Heat pump water heater | 2.20 UEF |

### Duct Leakage Testing

#### Requirements (FECC 403.3.5)
- **New construction**: Mandatory testing
- **Maximum leakage**: 4 CFM/100 sf @25 Pa
- **Ducts in conditioned space**: 4 CFM/100 sf or verification
- **Test report**: Required for permit

### Building Envelope (FECC Chapter 4)

#### Insulation Minimums (Residential)
| Component | Zone 1 | Zone 2 |
|-----------|--------|--------|
| Ceiling | R-38 | R-38 |
| Wood frame wall | R-13 | R-13 |
| Mass wall (CMU) | R-4 ci | R-4 ci |
| Floor over unconditioned | R-13 | R-13 |
| Basement wall | R-0 | R-0 |
| Slab edge | R-0 | R-0 |

#### Fenestration (Windows/Doors)
| Component | Zone 1 | Zone 2 |
|-----------|--------|--------|
| U-factor | 0.65 | 0.40 |
| SHGC | 0.25 | 0.25 |
| Skylight U-factor | 0.75 | 0.65 |
| Skylight SHGC | 0.30 | 0.30 |

### Mechanical Insulation

#### Pipe Insulation (FECC Table 403.2.10)
| Pipe Size | Heating | Cooling |
|-----------|---------|---------|
| < 1" | 1" | 0.5" |
| 1" - 1.5" | 1.5" | 0.75" |
| 2" - 4" | 1.5" | 1" |
| > 4" | 1.5" | 1.5" |

---

## Gas Systems (FBC Fuel Gas)

### Gas Piping

#### Pipe Sizing
Based on:
- Total BTU demand
- Length of run
- Inlet pressure
- Allowable pressure drop (0.5" w.c. typical)

#### Materials
| Location | Approved Materials |
|----------|-------------------|
| Exterior/underground | PE, coated steel |
| Interior | Black steel, CSST |
| Exposed locations | Schedule 40 black steel |

#### CSST Requirements
- **Bonding**: Direct bond to grounding electrode
- **Clearance**: Per manufacturer
- **Strike plates**: Where penetrating framing

### Gas Appliance Venting

#### Venting Categories
| Category | Description | Material |
|----------|-------------|----------|
| I | Negative pressure, non-condensing | B-vent, masonry |
| II | Negative pressure, condensing | AL29-4C stainless |
| III | Positive pressure, non-condensing | Special vent |
| IV | Positive pressure, condensing | PVC, CPVC, PP |

#### Termination Clearances
| Termination | Minimum Clearance |
|-------------|-------------------|
| To window/door (openable) | 4' horizontal, below |
| To window/door (openable) | 1' horizontal, above |
| To grade | 12" |
| To corner | 2' |
| To soffit | 1' |
| To forced air inlet | 10' |

### Combustion Air

#### Confined Spaces
Space with < 50 cu ft per 1,000 BTU/hr:
- **Option 1**: Two permanent openings (high/low)
  - Each opening: 1 sq in per 4,000 BTU (outdoor air)
- **Option 2**: Single opening
  - Direct to outdoors: 1 sq in per 3,000 BTU
  - Indirect: 1 sq in per 1,000 BTU
- **Option 3**: Mechanical air supply

#### Unconfined Spaces
- ≥ 50 cu ft per 1,000 BTU/hr
- Normal infiltration adequate

---

## Florida-Specific Requirements

### Hurricane/Wind
- **Equipment**: Strapped to resist design wind speed
- **HVHZ**: Enhanced requirements for Miami-Dade/Broward
- **Rooftop units**: Require product approval and engineered attachment

### Flood Zone
- **Electrical equipment**: Above BFE
- **HVAC equipment**: Above BFE or flood-resistant
- **Ductwork**: Above BFE or sealed

### Pool Pump Efficiency (Florida Specific)
- **Variable speed required**: For pools > 7 HP
- **Timer/controller**: Required on all pool pumps
- **Run time limits**: Per local utility programs

### Solar-Ready (FECC 403.5)

New residential construction:
- **Roof area**: Min 300 sf of unobstructed south-facing
- **Conduit**: 3/4" from roof to electrical panel area
- **Electrical**: Reserved space for 40A breaker
- **Plumbing**: Capped connections near water heater

---

## Quick Checklists

### Residential HVAC
- [ ] Equipment sized per Manual J/S/D
- [ ] Duct leakage test passed (≤4 CFM/100 sf)
- [ ] Insulation on all unconditioned ductwork
- [ ] Condensate drain with trap and secondary
- [ ] Hurricane strapping on outdoor unit
- [ ] Filter access per manufacturer
- [ ] Thermostat in neutral location

### Commercial HVAC
- [ ] Outdoor air per ASHRAE 62.1
- [ ] Exhaust rates per code
- [ ] Economizer if >54 kBtu/h (check exceptions)
- [ ] Energy recovery if >5,000 CFM OA
- [ ] Duct sealing per FECC
- [ ] Testing and balancing required
- [ ] Commissioning if >25,000 sf

### Electrical (Residential)
- [ ] Service sized per load calc
- [ ] GFCI at all required locations
- [ ] AFCI at all required locations
- [ ] Dedicated circuits per kitchen, laundry, HVAC
- [ ] Outdoor receptacles front and rear
- [ ] Pool/spa per NEC 680
- [ ] Surge protection at panel

### Commercial Kitchen
- [ ] Type I hood over grease-producing
- [ ] Fire suppression system
- [ ] Makeup air provision
- [ ] Exhaust rate per hood type
- [ ] Grease duct construction per code

---

*Reference: Florida Building Code 7th Edition (2023), NEC 2020, FECC 2020*
*Always verify with local AHJ for amendments and interpretations*

# HVAC Systems Design

## Load Calculations

### Cooling Load Factors
| Component | BTU/SF-hr |
|-----------|-----------|
| Roof (R-30) | 3-5 |
| Wall (R-13) | 2-4 |
| Window (single) | 40-60 |
| Window (double) | 20-35 |
| People (sensible) | 250 BTU/person |
| People (latent) | 200 BTU/person |
| Lighting | 3.41 BTU/watt |
| Equipment | 3.41 BTU/watt |

### Rules of Thumb
| Building Type | SF/Ton |
|---------------|--------|
| Residential | 400-600 |
| Office | 300-450 |
| Retail | 250-400 |
| Restaurant | 150-250 |
| Healthcare | 200-350 |
| Data center | 50-150 |
| Warehouse | 600-1,000 |

### Heating Load
| Climate Zone | BTU/SF |
|--------------|--------|
| Hot (FL, AZ) | 15-25 |
| Mixed | 25-40 |
| Cold | 40-60 |
| Very cold | 50-75 |

---

## System Types

### Residential Systems
| Type | Use |
|------|-----|
| Split system | Most common |
| Package unit | All-in-one outdoor |
| Mini-split | Ductless, zoning |
| Heat pump | Heating + cooling |
| Furnace + AC | Gas heat, electric cool |

### Commercial Systems
| Type | Application |
|------|-------------|
| Rooftop unit (RTU) | Small commercial |
| Split system | Small-medium |
| VAV | Medium-large office |
| VRF/VRV | Multi-zone |
| Chilled water | Large buildings |
| DOAS | Ventilation focus |
| Geothermal | High efficiency |

### Selection Criteria
| Factor | System Choice |
|--------|---------------|
| Small, simple | RTU or split |
| Zoning needed | VRF or VAV |
| High efficiency | VRF, geothermal |
| Large building | Chilled water + VAV |
| Retrofit | VRF or mini-splits |
| Critical spaces | Dedicated units |

---

## Duct Design

### Duct Sizing
| CFM | Round Size | Rectangular |
|-----|------------|-------------|
| 100 | 6" | 6×6 |
| 200 | 8" | 8×8 |
| 400 | 10" | 10×10 |
| 600 | 12" | 12×12 |
| 1,000 | 14" | 14×14 |
| 1,500 | 16" | 16×16 |
| 2,000 | 18" | 20×16 |
| 3,000 | 22" | 24×20 |
| 5,000 | 26" | 30×24 |

### Duct Velocities
| Application | FPM |
|-------------|-----|
| Main duct | 1,200-2,000 |
| Branch duct | 600-1,000 |
| Residential | 600-900 |
| Low noise areas | 400-600 |
| High velocity | 2,500-4,000 |

### Friction Loss
| Duct Type | Friction |
|-----------|----------|
| Galvanized | 0.08-0.12"/100' |
| Flex duct | 0.10-0.15"/100' |
| Fiberglass | 0.06-0.10"/100' |
| Spiral | 0.06-0.10"/100' |

### Duct Materials
| Material | Use |
|----------|-----|
| Galvanized steel | Standard supply/return |
| Aluminum | Kitchen exhaust |
| Stainless steel | Corrosive environments |
| Fiberglass duct board | Low velocity |
| Flex duct | Connections (max 6') |

---

## Diffusers and Grilles

### Diffuser Types
| Type | Application |
|------|-------------|
| Square ceiling | Standard offices |
| Slot | Linear ceiling |
| Round | Exposed ceilings |
| Perforated face | Low noise |
| Swirl | High CFM |
| VAV | Variable air volume |

### Diffuser Sizing
| CFM | Diffuser Size |
|-----|---------------|
| 50-100 | 6"×6" or 8"×8" |
| 100-200 | 10"×10" or 12"×12" |
| 200-400 | 12"×12" or 14"×14" |
| 400-600 | 18"×18" or 24"×24" |
| 600-1,000 | 24"×24" |

### Grille Types
| Type | Use |
|------|-----|
| Return grille | General return |
| Transfer grille | Door undercut |
| Bar grille | Floor return |
| Louver | Exterior intake/exhaust |
| Egg crate | Light-duty return |

---

## Ventilation

### Outdoor Air Requirements
| Space | CFM/Person | CFM/SF |
|-------|------------|--------|
| Office | 5 | 0.06 |
| Conference | 5 | 0.06 |
| Retail | 7.5 | 0.12 |
| Classroom | 10 | 0.12 |
| Restaurant | 7.5 | 0.18 |
| Healthcare | 15-25 | 0.06-0.12 |
| Gym | 20 | 0.18 |

### Exhaust Requirements
| Space | CFM |
|-------|-----|
| Toilet room | 50-75 CFM/fixture |
| Kitchen (residential) | 100-400 CFM |
| Kitchen (commercial) | Per hood |
| Janitor closet | 1 CFM/SF |
| Copy room | 0.50 CFM/SF |
| Parking garage | 0.75 CFM/SF |

### Kitchen Hood Exhaust
| Cooking Type | CFM/LF of Hood |
|--------------|----------------|
| Light (oven) | 150-200 |
| Medium (griddle) | 250-350 |
| Heavy (fryer, wok) | 350-550 |

---

## Controls

### Control Types
| Type | Application |
|------|-------------|
| Thermostat | Single zone |
| DDC | Building automation |
| BACnet | Commercial standard |
| Modbus | Industrial |
| Wireless | Retrofit |

### Setpoints
| Space | Cooling | Heating |
|-------|---------|---------|
| Office | 74-76°F | 68-70°F |
| Retail | 72-76°F | 68-70°F |
| Warehouse | 78-85°F | 55-60°F |
| Healthcare | 70-75°F | 68-72°F |
| Data center | 64-80°F | N/A |

### Energy Codes
| Code | Requirement |
|------|-------------|
| ASHRAE 90.1 | Commercial baseline |
| IECC | Residential + commercial |
| Title 24 (CA) | California energy |
| Florida Energy Code | Based on IECC |

---

## Equipment

### Rooftop Units
| Tonnage | CFM | Weight |
|---------|-----|--------|
| 3 | 1,200 | 500 lb |
| 5 | 2,000 | 700 lb |
| 7.5 | 3,000 | 950 lb |
| 10 | 4,000 | 1,200 lb |
| 15 | 6,000 | 1,800 lb |
| 20 | 8,000 | 2,400 lb |
| 25 | 10,000 | 3,000 lb |

### Chillers
| Type | Capacity | Efficiency |
|------|----------|------------|
| Air-cooled scroll | 20-200 tons | 10-12 EER |
| Air-cooled screw | 100-500 tons | 10-14 EER |
| Water-cooled screw | 100-1,500 tons | 0.5-0.6 kW/ton |
| Centrifugal | 200-3,000 tons | 0.4-0.6 kW/ton |
| Absorption | 100-1,500 tons | 0.7-1.0 COP |

### Boilers
| Type | Efficiency |
|------|------------|
| Standard | 80-82% |
| High efficiency | 85-90% |
| Condensing | 90-98% |

---

## Piping

### Chilled Water
| Tonnage | Pipe Size |
|---------|-----------|
| 10-20 | 2" |
| 20-50 | 3" |
| 50-100 | 4" |
| 100-200 | 6" |
| 200-400 | 8" |
| 400-700 | 10" |

### Hot Water
| MBH | Pipe Size |
|-----|-----------|
| 50-100 | 3/4" |
| 100-200 | 1" |
| 200-400 | 1-1/4" |
| 400-700 | 1-1/2" |
| 700-1,500 | 2" |
| 1,500-3,000 | 2-1/2" |

### Refrigerant
| System | Line Sets |
|--------|-----------|
| 2-3 ton split | 3/8" liquid, 3/4" suction |
| 4-5 ton split | 3/8" liquid, 7/8" suction |
| VRF | Per manufacturer |

---

## Air Quality

### Filtration
| MERV | Application |
|------|-------------|
| 1-4 | Residential (basic) |
| 6-8 | Commercial (standard) |
| 10-12 | Superior commercial |
| 13-16 | Hospital, clean room |
| 17-20 | HEPA |

### Humidity Control
| Space | RH Range |
|-------|----------|
| Office | 30-60% |
| Healthcare | 30-60% |
| Museum | 45-55% |
| Data center | 40-60% |
| Pool | 50-60% |

### Special Exhaust
| Application | System |
|-------------|--------|
| Laboratory | Fume hood |
| Healthcare | AII (negative) |
| Clean room | HEPA + positive |
| Industrial | Local exhaust |

---

## Sound and Vibration

### NC Levels
| Space | Max NC |
|-------|--------|
| Concert hall | 15-20 |
| Theater | 20-25 |
| Conference | 25-30 |
| Private office | 30-35 |
| Open office | 35-40 |
| Retail | 40-45 |

### Vibration Isolation
| Equipment | Isolation |
|-----------|-----------|
| AHU | Spring isolators |
| Chiller | Inertia base + springs |
| Pump | Inertia base |
| Fan | Vibration isolators |
| Ductwork | Flexible connections |

---

## Energy Recovery

### Types
| Type | Effectiveness |
|------|---------------|
| Total enthalpy wheel | 70-80% |
| Sensible wheel | 65-75% |
| Plate heat exchanger | 50-70% |
| Run-around coil | 40-60% |
| Heat pipe | 50-65% |

### When Required
| Climate | OA CFM |
|---------|--------|
| All climates | > 5,000 CFM at 70%+ OA |
| Varies by code | Check local requirements |

---

## Clearances

### Equipment Access
| Equipment | Front | Sides |
|-----------|-------|-------|
| AHU | 36" | 24" |
| RTU | 36" | 24" |
| Boiler | 36" | 24" |
| Chiller | 36"+ | Tube pull |

### Ceiling Space
| System | Height Needed |
|--------|---------------|
| VAV with duct | 24"-36" |
| Fan coil | 18"-24" |
| Mini-split | 12"-18" |
| Chilled beam | 18"-24" |

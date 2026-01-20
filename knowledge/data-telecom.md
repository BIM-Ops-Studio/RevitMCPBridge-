# Data and Telecommunications Systems

## Infrastructure Planning

### Space Allocation
| Space | Size | Use |
|-------|------|-----|
| Main Equipment Room (MER) | 150-300 SF | Building entrance, servers |
| Telecom Room (TR) | 100-150 SF | Floor distribution |
| Telecom Closet | 50-80 SF | Small floors |

### Room Requirements
| Feature | Requirement |
|---------|-------------|
| Location | Central to floor |
| Stacking | Vertically aligned preferred |
| Coverage | Max 295' cable run |
| Height | 9'-0" minimum |
| Door | 36" min, swing out |
| Power | Dedicated circuits |
| Cooling | 24/7, 64-75°F |
| Access | Secure, limited |

### One Room Per
| Building Area | Rooms Required |
|---------------|----------------|
| 10,000 SF | 1 per floor |
| 20,000 SF | 1-2 per floor |
| 50,000 SF | 2-3 per floor |

---

## Cabling Standards

### Horizontal Cabling
| Category | Speed | Max Distance |
|----------|-------|--------------|
| Cat5e | 1 Gbps | 100m (328') |
| Cat6 | 10 Gbps | 55m @ 10G |
| Cat6A | 10 Gbps | 100m (328') |
| Cat8 | 25-40 Gbps | 30m |

### Fiber Optic
| Type | Speed | Distance |
|------|-------|----------|
| OM3 (multimode) | 10 Gbps | 300m |
| OM4 (multimode) | 10 Gbps | 400m |
| OM5 (multimode) | 100 Gbps | 150m |
| OS2 (singlemode) | 100+ Gbps | 10+ km |

### Cable Counts
| Space Type | Drops per Position |
|------------|-------------------|
| Office (standard) | 2-3 |
| Office (trading) | 4-6 |
| Conference room | 4-8 |
| Classroom | 2-4 per table |
| Healthcare | 3-6 per room |
| Hotel room | 2-4 |

---

## Pathway Systems

### Horizontal Pathways
| Type | Capacity |
|------|----------|
| Cable tray | High volume |
| Conduit | Protection, separation |
| J-hooks | Light duty |
| Innerduct | Flexible routing |

### Conduit Fill
| Size | Max Cables |
|------|------------|
| 3/4" | 3-4 Cat6 |
| 1" | 5-6 Cat6 |
| 1-1/4" | 8-10 Cat6 |
| 2" | 15-20 Cat6 |

### Backbone Pathways
| Between | Pathway Type |
|---------|--------------|
| Floors | Sleeves, slots |
| Buildings | Underground, aerial |
| MER to TR | Conduit, tray |

### Sleeve Sizing
| Cables | Sleeve Size |
|--------|-------------|
| 1-12 | 2" |
| 13-36 | 3" |
| 37-72 | 4" |
| 72+ | Multiple or slot |

---

## Wireless Systems

### WiFi Planning
| Coverage | AP Spacing |
|----------|------------|
| Light use | 2,500-3,500 SF |
| Medium use | 1,500-2,500 SF |
| High density | 800-1,500 SF |
| Stadium/auditorium | Per design |

### AP Requirements
| Feature | Requirement |
|---------|-------------|
| Power | PoE (802.3at or .bt) |
| Data | Cat6A minimum |
| Mounting | Ceiling or wall |
| Height | 8'-12' AFF |
| Clearance | 20' from other APs |

### DAS (Distributed Antenna System)
| Use | When Required |
|-----|---------------|
| Cellular coverage | Interior > 50,000 SF |
| First responder | Per code |
| Deep interior | No cellular signal |

---

## Audio Visual Systems

### Display Sizing
| Viewing Distance | Screen Size |
|------------------|-------------|
| 8' | 55"-65" |
| 12' | 65"-85" |
| 15' | 85"-100" |
| 20'+ | Projector or LED wall |

### Conference Room AV
| Room Size | Equipment |
|-----------|-----------|
| Huddle (2-4) | Display, camera, speaker |
| Small (6-8) | Display, PTZ camera, soundbar |
| Medium (10-16) | Display/projector, ceiling mics |
| Large (20+) | Projector, multiple displays, ceiling mics |

### Infrastructure for AV
| Item | Requirement |
|------|-------------|
| Display | 2-3 outlets, data drop |
| Projector | Dedicated circuit, data |
| Control | Network connection |
| Ceiling mics | Cat6 to each |
| Speakers | Speaker wire or network |

---

## Security Integration

### Access Control
| Component | Cabling |
|-----------|---------|
| Card reader | 2-pair + Cat6 |
| Door controller | Cat6 |
| Electric lock | 2-pair |
| REX sensor | 2-pair |
| Door contact | 2-pair |

### CCTV/IP Cameras
| Camera Type | Bandwidth |
|-------------|-----------|
| 1080p | 4-8 Mbps |
| 4MP | 8-12 Mbps |
| 4K (8MP) | 12-20 Mbps |

### Cable Requirements
| Device | Cable |
|--------|-------|
| IP camera | Cat6A (PoE+) |
| Analog camera | Coax RG-6 |
| Access panel | Cat6 |
| Intercom | Cat6 or 2-pair |

---

## Server and Data Rooms

### Power Density
| Use | W/SF |
|-----|------|
| Telecom closet | 20-30 |
| Server room | 50-100 |
| Data center | 100-300 |
| High-density | 300-500 |

### Cooling Requirements
| Heat Load | Cooling |
|-----------|---------|
| 1 kW | 0.28 tons |
| 5 kW | 1.4 tons |
| 10 kW | 2.8 tons |
| 20 kW | 5.7 tons |

### Rack Spacing
| Configuration | Spacing |
|---------------|---------|
| Hot/cold aisle | 4'-6' between rows |
| Front clearance | 42" minimum |
| Rear clearance | 36" minimum |

### Power per Rack
| Density | Power |
|---------|-------|
| Low | 3-5 kW |
| Medium | 5-10 kW |
| High | 10-20 kW |
| Ultra-high | 20-50 kW |

---

## Grounding and Bonding

### Telecom Grounding
| Component | Requirement |
|-----------|-------------|
| TGB (Telecom Ground Busbar) | In each TR |
| TBB (Telecom Bonding Backbone) | Links all TGBs |
| Size (TGB) | 4" × 1/4" copper |
| Size (TBB) | 3/0 minimum |

### Bonding Requirements
| Item | Bond To |
|------|---------|
| Cable trays | TGB |
| Racks | TGB |
| Equipment | TGB |
| Conduit | Per NEC |

---

## Design Documentation

### Drawings Required
| Drawing | Content |
|---------|---------|
| Riser diagram | Backbone topology |
| Floor plan | Outlet locations |
| TR layout | Equipment placement |
| Pathway | Conduit, tray routes |
| Details | Mounting, connections |

### Specifications
| Section | Content |
|---------|---------|
| 27 05 00 | Common work results |
| 27 10 00 | Structured cabling |
| 27 13 00 | Communications backbone |
| 27 15 00 | Communications horizontal |
| 27 20 00 | Data communications |
| 27 40 00 | Audio-video |

---

## Standards and Codes

### Key Standards
| Standard | Scope |
|----------|-------|
| TIA-568 | Commercial cabling |
| TIA-569 | Pathways and spaces |
| TIA-606 | Administration |
| TIA-607 | Grounding and bonding |
| BICSI | Design guidelines |

### Testing
| Test | For |
|------|-----|
| Wire map | Correct termination |
| Length | Max distance |
| Insertion loss | Signal attenuation |
| NEXT | Crosstalk |
| Return loss | Impedance |
| Certification | Full channel test |

---

## Labeling

### Label Requirements
| Item | Label Content |
|------|---------------|
| Cable (both ends) | Unique ID |
| Patch panel port | Port number |
| Outlet | Room + port |
| Pathway | System identification |
| TR door | Room designation |

### Color Coding (Example)
| Color | Use |
|-------|-----|
| Blue | Voice |
| White | Data |
| Orange | Fiber |
| Green | Network/CCTV |
| Red | Fire alarm (not telecom) |

---

## Future Considerations

### Emerging Technologies
| Technology | Infrastructure Need |
|------------|---------------------|
| 5G/Wi-Fi 6E | More APs, fiber backbone |
| IoT | Additional outlets, PoE |
| AV over IP | High bandwidth, QoS |
| Cloud services | Reliable WAN |
| Edge computing | Local server space |

### Spare Capacity
| Component | Recommendation |
|-----------|----------------|
| Conduit fill | 40% initial max |
| Patch panel | 25% spare ports |
| Cable tray | 25-50% spare |
| TR space | Room for growth |

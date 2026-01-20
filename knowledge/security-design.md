# Security Systems Design

## Access Control Systems

### System Components
| Component | Function |
|-----------|----------|
| Controller | Brain - processes credentials |
| Reader | Input device - card, fob, keypad |
| Electric lock | Output - latch, strike, maglock |
| REX | Request to exit sensor |
| Door position | Monitor open/closed |
| Power supply | 12V or 24V DC |

### Reader Technologies
| Type | Security Level | Use |
|------|----------------|-----|
| Proximity (125 kHz) | Low | Legacy, basic access |
| Smart card (13.56 MHz) | Medium | Corporate standard |
| Mobile credential | Medium-High | Modern convenience |
| Biometric | High | Sensitive areas |
| Multi-factor | Highest | Critical infrastructure |

### Door Hardware
| Lock Type | Hold Force | Use |
|-----------|-----------|-----|
| Electric strike | Varies | Standard doors |
| Magnetic lock | 600-1200 lb | Glass doors, high security |
| Electric latch | Same as hardware | Panic hardware |
| Electrified mortise | Same as hardware | Heavy-duty |

### Power Requirements
| Device | Power | Notes |
|--------|-------|-------|
| Maglocks | 12/24V DC, 300-600mA | Fail-safe (unlock on power loss) |
| Electric strikes | 12/24V DC, 200-400mA | Fail-secure or fail-safe |
| Readers | 12V DC, 100-200mA | Low power |
| Controllers | 12V DC, 500mA-2A | Plus battery backup |

---

## Video Surveillance (CCTV)

### Camera Types
| Type | Use | Field of View |
|------|-----|---------------|
| Fixed box | Indoor general | 60°-90° |
| Dome | Vandal resistance | 80°-110° |
| PTZ | Active monitoring | 360° pan, 90° tilt |
| Bullet | Outdoor/distance | 30°-60° |
| Fisheye | 360° coverage | 180°-360° |

### Resolution Standards
| Resolution | Pixels | Use |
|------------|--------|-----|
| 1080p (2MP) | 1920×1080 | General surveillance |
| 4MP | 2560×1440 | Detailed coverage |
| 4K (8MP) | 3840×2160 | Facial recognition, license plates |
| 12MP | 4000×3000 | Large area overview |

### Coverage Guidelines
| Area | PPF Required | Notes |
|------|--------------|-------|
| Detection | 20-40 PPF | Person present |
| Recognition | 40-80 PPF | Identify known person |
| Identification | 80-120 PPF | ID unknown person |
| Forensic | 120+ PPF | Facial recognition |

PPF = Pixels Per Foot (horizontal target width)

### Storage Calculations
```
Storage (GB) = Cameras × Bitrate (Mbps) × Hours × Days × 0.0045

Example:
16 cameras × 4 Mbps × 24 hr × 30 days × 0.0045 = 2,073 GB
```

### Retention Requirements
| Facility | Retention |
|----------|-----------|
| Retail | 30 days |
| Commercial office | 30-60 days |
| Banking | 90 days |
| Gaming | 7-30 days (varies by jurisdiction) |
| Critical infrastructure | 90+ days |

---

## Intrusion Detection

### Sensor Types
| Sensor | Use | Coverage |
|--------|-----|----------|
| Door contact | Entry points | Per door |
| Glass break | Windows | 20'-35' radius |
| PIR motion | Interior spaces | 40'-60' × 40'-60' |
| Dual-tech | Reduce false alarms | 40' × 40' |
| Photoelectric beam | Perimeter | 100'-700' |
| Microwave | Large open areas | 100' × 50' |

### Zone Types
| Zone | Response |
|------|----------|
| Entry/Exit | Delay for arming/disarming |
| Instant | Immediate alarm |
| Interior | Follows entry delay |
| 24-hour | Always armed (fire, panic) |
| Supervisory | Trouble only (tamper) |

### Panel Capacity
| Size | Zones | Use |
|------|-------|-----|
| Small | 8-16 | Residential |
| Medium | 32-64 | Small commercial |
| Large | 128+ | Large commercial |
| Enterprise | Unlimited | Campus, multi-site |

---

## Fire Alarm Integration

### Interface with Security
| Integration | Purpose |
|-------------|---------|
| Door release | Unlock on fire alarm |
| Elevator recall | Return to ground floor |
| CCTV | Switch to fire views |
| Access control | Unlock egress paths |
| Mass notification | Broadcast alerts |

### Door Unlock Requirements
- Fail-safe locks on egress doors
- Fire alarm releases all locks in fire zone
- Delayed egress (15-30 sec) allowed with conditions

---

## Physical Security Design

### Layers of Protection
```
Layer 1: Perimeter (fence, gates, barriers)
Layer 2: Building envelope (doors, windows, walls)
Layer 3: Interior (access control, CCTV)
Layer 4: Critical assets (safes, cages, vaults)
```

### Site Security
| Element | Purpose |
|---------|---------|
| Fencing | Define boundary, delay |
| Gates | Controlled vehicle entry |
| Bollards | Vehicle barrier |
| Lighting | Visibility, deterrence |
| Landscaping | Eliminate hiding spots |

### Lighting Levels
| Area | Foot-candles |
|------|--------------|
| Parking lot | 1-5 FC |
| Perimeter | 0.5-2 FC |
| Building entrance | 5-10 FC |
| Loading dock | 5-10 FC |
| Critical areas | 10-20 FC |

### Barrier Ratings
| Rating | Vehicle | Speed |
|--------|---------|-------|
| K4 | 15,000 lb | 30 mph |
| K8 | 15,000 lb | 40 mph |
| K12 | 15,000 lb | 50 mph |

---

## Security Room/Command Center

### Space Requirements
| Function | Size |
|----------|------|
| 2-operator console | 150-200 SF |
| 4-operator console | 300-400 SF |
| Server/head-end | 100-200 SF |
| Break room | As needed |

### Environment
| Parameter | Requirement |
|-----------|-------------|
| Temperature | 68-72°F |
| Humidity | 40-50% RH |
| Lighting | Dimmable, indirect |
| Acoustics | NC-35 or better |
| Power | UPS protected |

### Video Wall Sizing
| Displays | Viewing Distance |
|----------|------------------|
| 4 × 55" | 8'-10' |
| 6 × 55" | 10'-12' |
| 9 × 55" | 12'-15' |

---

## Network Infrastructure

### Security Network Design
| Principle | Implementation |
|-----------|----------------|
| Segmentation | Separate VLAN for security |
| Encryption | TLS for all traffic |
| Redundancy | Dual paths, failover |
| Bandwidth | 10-15 Mbps per camera |
| Storage | RAID arrays, offsite backup |

### PoE Requirements
| Device | PoE Class | Watts |
|--------|-----------|-------|
| Standard camera | Class 3 | 15W |
| PTZ camera | Class 4 | 25W |
| Card reader | Class 1 | 4W |
| Intercom | Class 3 | 13W |

### Cabling
| Cable | Distance | Use |
|-------|----------|-----|
| Cat6 | 328' (100m) | IP devices |
| Cat6A | 328' (100m) | PoE++, high bandwidth |
| Fiber (MM) | 1,800' | Building backbone |
| Fiber (SM) | Miles | Campus, WAN |

---

## Door Types by Security Level

### Low Security
- Card reader only
- Electric strike
- Standard door
- No monitoring

### Medium Security
- Card + PIN
- Electric strike or maglock
- Door position switch
- CCTV coverage

### High Security
- Multi-factor (card + biometric)
- Magnetic lock or electrified mortise
- Door position + REX
- Mantrap/interlock possible
- CCTV with recording

### Maximum Security
- Multi-factor + escort
- Portal/mantrap required
- Anti-passback
- Weight/occupancy sensors
- Continuous CCTV monitoring

---

## Code Requirements

### Fire/Life Safety
- Egress doors: Fail-safe (unlock on fire alarm)
- Delayed egress: Max 15-30 seconds
- Exit signage: Must remain visible
- Panic hardware: Required on assembly egress

### ADA Considerations
- Card readers: 48" max AFF
- Keypad: Accessible reach range
- Automatic openers: May be required
- Door force: 5 lb max to open

### Local Requirements
| Requirement | Source |
|-------------|--------|
| Fire alarm connection | Fire marshal |
| Alarm response | Local police |
| Camera placement | Privacy laws |
| Recording consent | State law |
| False alarm fees | Municipality |

---

## System Integration

### Common Integrations
| System A | System B | Integration |
|----------|----------|-------------|
| Access control | CCTV | Camera call-up on door event |
| Access control | Intrusion | Arm/disarm by credential |
| CCTV | Fire alarm | Preset camera positions |
| Access control | Elevator | Floor access control |
| All systems | BMS | Facility management |

### Integration Protocols
| Protocol | Use |
|----------|-----|
| ONVIF | IP cameras |
| OSDP | Access control |
| BACnet | Building automation |
| API/REST | Custom integration |
| RTSP | Video streaming |

---

## Drawing Requirements

### Security Plans Show
- [ ] Camera locations with coverage arcs
- [ ] Card reader locations
- [ ] Door hardware schedule
- [ ] Conduit paths
- [ ] Head-end equipment location
- [ ] Power supply locations

### Riser Diagrams Show
- [ ] Controller hierarchy
- [ ] Network topology
- [ ] Power distribution
- [ ] Integration points

### Schedules
- Door hardware schedule
- Camera schedule (type, lens, mounting)
- Access level matrix
- Intercom schedule

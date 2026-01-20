# Data Center Design

## Tier Classifications

### Uptime Institute Tiers
| Tier | Availability | Downtime/Year | Redundancy |
|------|--------------|---------------|------------|
| Tier I | 99.671% | 28.8 hours | N (no redundancy) |
| Tier II | 99.741% | 22 hours | N+1 (partial) |
| Tier III | 99.982% | 1.6 hours | N+1 (concurrent) |
| Tier IV | 99.995% | 0.4 hours | 2N or 2N+1 |

### Tier Requirements
| Feature | Tier I | Tier II | Tier III | Tier IV |
|---------|--------|---------|----------|---------|
| Power path | Single | Single | Active + alternate | 2 active |
| Cooling path | Single | Single + backup | Active + alternate | 2 active |
| Concurrent maintenance | No | No | Yes | Yes |
| Fault tolerance | No | No | No | Yes |

---

## Power Systems

### Power Architecture
| Component | Function |
|-----------|----------|
| Utility feed | Primary power source |
| Switchgear | Distribution, protection |
| Transformer | Voltage conversion |
| Generator | Backup power |
| UPS | Uninterruptible supply |
| PDU | Power distribution unit |
| RPP | Remote power panel |

### Power Density
| Era | Power per Rack |
|-----|----------------|
| Traditional | 5-7 kW |
| Modern | 10-15 kW |
| High-density | 20-30 kW |
| Ultra-high | 40-60+ kW |
| AI/HPC | 100+ kW |

### Efficiency Metrics
| Metric | Target |
|--------|--------|
| PUE | 1.2-1.6 |
| DCiE | 60-80% |
| Carbon usage (CUE) | < 0.5 |
| Water usage (WUE) | < 1.8 L/kWh |

### PUE Calculation
```
PUE = Total Facility Power / IT Equipment Power

Example:
2.0 MW total / 1.0 MW IT = PUE 2.0

Target:
< 1.4 = Efficient
< 1.2 = Best in class
```

---

## Cooling Systems

### Cooling Methods
| Method | Application | Efficiency |
|--------|-------------|------------|
| Computer room air conditioning (CRAC) | Traditional | Lower |
| Computer room air handler (CRAH) | Modern | Medium |
| In-row cooling | High-density | Higher |
| Rear door heat exchanger | Very high-density | High |
| Liquid cooling (direct) | HPC, AI | Highest |
| Free cooling (economizer) | Climate-dependent | Variable |

### Cooling Configurations
| Type | Description |
|------|-------------|
| Raised floor plenum | Underfloor air supply |
| Hot aisle/cold aisle | Row orientation |
| Cold aisle containment | Enclosed supply aisle |
| Hot aisle containment | Enclosed return aisle |
| Chimney/cabinet | Individual containment |

### Temperature Standards
| Parameter | ASHRAE A1 | ASHRAE A2 |
|-----------|-----------|-----------|
| Recommended range | 64-80°F | 50-95°F |
| Allowable range | 59-90°F | 41-113°F |
| Humidity | 20-80% RH | 20-80% RH |
| Dewpoint | 42-59°F | 42-69°F |

### Cooling Calculations
| Factor | Value |
|--------|-------|
| Heat output | 3.41 BTU/hr per Watt |
| 1 ton cooling | 12,000 BTU/hr = 3.5 kW |
| CFM per kW | 150-200 CFM |
| Delta-T | 15-25°F |

---

## Space Planning

### White Space Layout
| Element | Dimension |
|---------|-----------|
| Row spacing | 4'-6' (cold aisle) |
| Hot aisle | 3'-4' |
| Perimeter | 3' minimum |
| Ceiling height | 10'-14' |
| Raised floor | 18"-48" |

### Rack Standards
| Dimension | Standard |
|-----------|----------|
| Width | 19" (EIA-310) |
| Height | 42U-52U typical |
| Depth | 36"-48" |
| Spacing | 42" rail centers |
| Weight | 2,000-3,000 lbs |

### Density Planning
| Density | W/SF | Racks/1000 SF |
|---------|------|---------------|
| Low | 50-100 | 10-15 |
| Medium | 100-150 | 15-25 |
| High | 150-250 | 25-40 |
| Ultra-high | 250+ | 40+ |

---

## Electrical Infrastructure

### Voltage Standards
| Level | Voltage | Application |
|-------|---------|-------------|
| Medium voltage | 4160V, 12-15kV | Utility, generator |
| Low voltage | 480V, 208V | Distribution |
| IT equipment | 208V, 120V | Servers, storage |

### UPS Configurations
| Type | Description |
|------|-------------|
| Centralized | Large UPS for entire facility |
| Distributed | Multiple smaller UPS |
| Pod-based | UPS per row or zone |
| Rack-mounted | UPS in each rack |

### Generator Sizing
| Load Type | Runtime |
|-----------|---------|
| Life safety | 2 hours |
| Tier II | 12-24 hours |
| Tier III | 24-72 hours |
| Tier IV | 72+ hours |
| Fuel on-site | Per tier + refuel plan |

### Redundancy Levels
| Configuration | Description |
|---------------|-------------|
| N | No redundancy |
| N+1 | One spare unit |
| 2N | Full duplicate |
| 2N+1 | Full duplicate + spare |
| Catcher systems | Isolated power paths |

---

## Fire Protection

### Detection Systems
| Type | Application |
|------|-------------|
| VESDA | Very early warning |
| Spot detection | Under floor, ceiling |
| Beam detection | High ceilings |
| Aspirating | Continuous sampling |

### Suppression Systems
| Agent | Application | Considerations |
|-------|-------------|----------------|
| FM-200 | Clean agent | Ceiling height limits |
| Novec 1230 | Clean agent | Low GWP |
| Inergen | Inert gas | Safe for occupants |
| Water mist | Alternative | Reduced water damage |
| Pre-action | Water with safeguards | Dual verification |

### Fire Protection Strategies
| Strategy | Description |
|----------|-------------|
| Compartmentalization | 2-hour fire walls |
| Sprinkler zoning | Limit water exposure |
| Detection-first | Early warning priority |
| Abort capabilities | Cancel discharge |

---

## Physical Security

### Security Layers
| Layer | Controls |
|-------|----------|
| Perimeter | Fencing, cameras, lighting |
| Building | Card access, mantrap |
| White space | Biometric, escort |
| Rack level | Cabinet locks, cameras |

### Access Control
| Zone | Requirements |
|------|--------------|
| Public areas | Badge required |
| Offices | Badge + PIN |
| Data hall | Badge + biometric |
| Critical areas | Two-person rule |

### Surveillance
| Area | Coverage |
|------|----------|
| Exterior | 100% coverage |
| Entry points | High resolution |
| Data hall | All aisles |
| Equipment | Critical racks |
| Retention | 90+ days |

---

## Environmental Monitoring

### Monitored Parameters
| Parameter | Sensors |
|-----------|---------|
| Temperature | Throughout |
| Humidity | Room level |
| Water detection | Under floor |
| Power | Per circuit |
| Airflow | CRAC/CRAH, cabinets |

### Alarm Thresholds
| Parameter | Warning | Critical |
|-----------|---------|----------|
| Temperature high | 80°F | 90°F |
| Temperature low | 60°F | 50°F |
| Humidity high | 70% | 80% |
| Humidity low | 30% | 20% |
| Water | Any detection | - |

### DCIM (Data Center Infrastructure Management)
| Function | Capability |
|----------|------------|
| Asset management | Track equipment |
| Capacity planning | Power, space, cooling |
| Environmental | Real-time monitoring |
| Change management | Document moves |
| Reporting | Metrics, trends |

---

## Network Infrastructure

### Cabling Standards
| Cable Type | Application |
|------------|-------------|
| Cat 6A | Copper, 10 Gbps |
| OM4 | Multimode fiber, 100 Gbps |
| OS2 | Single-mode fiber, long haul |
| Direct attach | Short rack connections |

### Cable Management
| Element | Purpose |
|---------|---------|
| Cable trays | Overhead distribution |
| Under-floor | Raised floor routing |
| Ladder rack | Vertical distribution |
| Fiber ducts | Fiber protection |

### Meet-Me Rooms
| Feature | Purpose |
|---------|---------|
| Carrier neutral | Multiple providers |
| Cross-connects | Interconnection |
| Demarcation | Handoff points |
| Security | Controlled access |

---

## Commissioning

### Cx Phases
| Phase | Activities |
|-------|------------|
| Design review | Verify redundancy, capacity |
| Factory witness | Test major equipment |
| Installation verification | Inspect installation |
| Functional testing | Individual systems |
| Integrated systems | Combined operation |
| Failure testing | Simulate failures |

### Critical Tests
| Test | Purpose |
|------|---------|
| UPS battery | Verify runtime |
| Generator load bank | Verify capacity |
| ATS transfer | Verify transfer time |
| Cooling failure | Verify backup |
| Full load | Verify combined operation |

### Failure Mode Testing
| Scenario | Expected Result |
|----------|-----------------|
| Utility loss | Generator starts, UPS bridges |
| Generator failure | Second unit starts |
| CRAC failure | Backup cooling activates |
| UPS failure | Bypass or redundant path |
| Fire detection | Proper response |

---

## Sustainability

### Efficiency Strategies
| Strategy | Impact |
|----------|--------|
| Free cooling | Reduce mechanical cooling |
| Hot aisle containment | Improve cooling efficiency |
| Higher set points | Reduce cooling load |
| Efficient UPS | Higher conversion efficiency |
| LED lighting | Reduce lighting load |

### Renewable Energy
| Source | Application |
|--------|-------------|
| On-site solar | Rooftop, carports |
| PPA | Off-site renewable |
| RECs | Carbon offset |
| Battery storage | Peak shaving |

### Water Conservation
| Strategy | Impact |
|----------|--------|
| Air-cooled chillers | Eliminate cooling towers |
| Dry coolers | Reduce water use |
| Reclaimed water | Cooling towers |
| Water-side economizer | Reduce chiller hours |

---

## Edge Data Centers

### Characteristics
| Feature | Edge | Enterprise |
|---------|------|------------|
| Size | 100-500 kW | 1-50 MW |
| Latency | < 5ms | Variable |
| Location | Distributed | Centralized |
| Staffing | Remote | On-site |
| Build | Modular, prefab | Traditional |

### Edge Considerations
| Factor | Requirement |
|--------|-------------|
| Physical security | Unmanned operation |
| Remote management | Full visibility |
| Reliability | Self-healing |
| Serviceability | Quick swap components |
| Environmental | Wide temperature range |

---

## Cost Factors

### Capital Costs
| Component | $/kW IT |
|-----------|---------|
| Tier II | $8,000-12,000 |
| Tier III | $15,000-22,000 |
| Tier IV | $22,000-35,000 |
| Total build-out | $600-1,200/SF |

### Operating Costs
| Item | % of Total |
|------|------------|
| Power | 50-60% |
| Personnel | 15-25% |
| Maintenance | 10-15% |
| Other | 10-15% |

### Power Costs
| Metric | Calculation |
|--------|-------------|
| Annual kWh | kW × 8,760 hours × PUE |
| Cost | kWh × utility rate |
| Per rack | Annual cost / number of racks |

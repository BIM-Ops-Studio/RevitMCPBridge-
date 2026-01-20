# Emergency and Backup Power Systems

## System Types

### Power Source Comparison
| Type | Start Time | Duration | Cost |
|------|------------|----------|------|
| Generator (diesel) | 10 seconds | Unlimited (fuel) | $$$ |
| Generator (natural gas) | 10 seconds | Unlimited (supply) | $$$ |
| UPS (battery) | Instant | 5-30 minutes | $$ |
| UPS + generator | Instant | Unlimited | $$$$ |
| Fuel cell | Varies | Unlimited (fuel) | $$$$ |
| Solar + battery | Instant | Hours | $$$$ |

### By Application
| Application | Typical System |
|-------------|----------------|
| Data center | UPS + generator |
| Hospital | Generator + UPS (critical) |
| Office building | Generator |
| Residential | Portable or standby |
| Life safety | Generator |
| Industrial | Generator + UPS |

---

## Generator Systems

### Fuel Types
| Fuel | Pros | Cons |
|------|------|------|
| Diesel | High power, reliable | Storage, emissions |
| Natural gas | Clean, unlimited supply | Lower power density |
| Propane (LP) | Clean, storable | Tank required |
| Bi-fuel | Flexibility | Complexity |

### Sizing Methodology
| Step | Action |
|------|--------|
| 1 | List all emergency loads |
| 2 | Determine kW for each |
| 3 | Apply load factors |
| 4 | Add for motor starting |
| 5 | Add 20-25% margin |

### Typical Emergency Loads
| Load Category | Description |
|---------------|-------------|
| Life safety | Exit lighting, fire alarm, smoke control |
| Critical | Elevators, refrigeration, medical |
| Optional standby | HVAC, lighting, equipment |
| Code-required | Per NEC Article 700, 701, 702 |

### Generator Sizing (Rules of Thumb)
| Building Type | kW/1000 SF |
|---------------|------------|
| Office | 3-5 |
| Hospital | 8-15 |
| Data center | 50-150 |
| Retail | 2-4 |
| Hotel | 3-5 |
| Residential (multi-family) | 2-3 |

---

## Generator Components

### Engine and Alternator
| Component | Function |
|-----------|----------|
| Engine | Prime mover (diesel/gas) |
| Alternator | Generates electricity |
| Governor | Controls speed |
| Voltage regulator | Maintains voltage |
| Cooling system | Radiator, fan |
| Exhaust system | Muffler, discharge |

### Fuel System
| Component | Purpose |
|-----------|---------|
| Day tank | Immediate supply (1-8 hours) |
| Main tank | Bulk storage |
| Transfer pump | Day tank fill |
| Fuel filters | Contamination removal |
| Fuel return | Excess fuel circulation |
| Fuel polishing | Long-term maintenance |

### Control and Monitoring
| Feature | Function |
|---------|----------|
| Auto-start | Start on power loss |
| Transfer switch | Switch to generator |
| Paralleling | Multiple generators |
| Load shedding | Protect from overload |
| Remote monitoring | SCADA, BMS integration |
| Exerciser | Automatic testing |

---

## Transfer Switches

### Types
| Type | Description | Transfer Time |
|------|-------------|---------------|
| Automatic (ATS) | Senses loss, transfers | 10-30 seconds |
| Manual | Operator transfers | Minutes |
| Static (STS) | Solid-state | 4-8 milliseconds |
| Bypass isolation | Maintenance capability | N/A |

### Transfer Configurations
| Configuration | Description |
|---------------|-------------|
| Open transition | Break-before-make |
| Closed transition | Make-before-break (brief parallel) |
| Soft load transfer | Ramp transfer |
| Load shedding | Drops non-critical |

### ATS Ratings
| Rating | Typical Application |
|--------|---------------------|
| 100A | Small commercial |
| 200A | Medium commercial |
| 400A | Larger loads |
| 800A | Large commercial |
| 1200A+ | Major facilities |
| 4000A+ | Hospitals, data centers |

---

## UPS Systems

### UPS Types
| Type | Description | Efficiency |
|------|-------------|------------|
| Offline (standby) | Switches on failure | 95-98% |
| Line-interactive | Conditions power | 95-98% |
| Online (double-conversion) | Always on battery | 90-95% |
| Rotary | Flywheel, generator | 95-97% |

### Battery Technologies
| Type | Pros | Cons |
|------|------|------|
| VRLA (sealed lead-acid) | Cost, proven | Weight, life |
| Flooded lead-acid | Long life | Maintenance, space |
| Lithium-ion | Compact, long life | Cost |
| Nickel-cadmium | Long life, reliable | Cost, disposal |

### UPS Sizing
| Factor | Consideration |
|--------|---------------|
| Load (kVA) | Sum of connected equipment |
| Power factor | Typically 0.8-0.9 |
| Runtime | Minutes required |
| Redundancy | N+1, 2N |
| Future growth | 20-30% margin |

### Runtime vs Battery
| Runtime | Battery Multiplier |
|---------|-------------------|
| 5 minutes | 1× |
| 10 minutes | 2× |
| 15 minutes | 3× |
| 30 minutes | 6× |

---

## Code Requirements

### NEC Article 700 - Emergency
| Requirement | Description |
|-------------|-------------|
| Power source | Required for life safety |
| Transfer time | 10 seconds maximum |
| Duration | 1.5 hours minimum |
| Fuel | On-site for duration |
| Testing | Monthly, load annually |

### NEC Article 701 - Legally Required Standby
| Requirement | Description |
|-------------|-------------|
| Power source | For property protection |
| Transfer time | 60 seconds maximum |
| Duration | As required |
| Testing | Periodic |

### NEC Article 702 - Optional Standby
| Requirement | Description |
|-------------|-------------|
| Power source | For convenience |
| Transfer time | Not specified |
| Duration | As desired |
| Testing | Per manufacturer |

### Florida-Specific (Healthcare)
| Requirement | Standard |
|-------------|----------|
| Runtime | 96 hours minimum (nursing homes) |
| Fuel | On-site for 96 hours |
| Annual testing | Full load |
| Generator room | Per NFPA 110 |

---

## Installation Requirements

### Generator Room
| Element | Requirement |
|---------|-------------|
| Fire rating | 2-hour typically |
| Ventilation | Combustion + cooling air |
| Exhaust | To outdoors |
| Fuel storage | Per fire code |
| Sound | Attenuation as needed |
| Access | For maintenance |

### Outdoor Installation
| Element | Requirement |
|---------|-------------|
| Enclosure | Weather-protective |
| Setbacks | Per code |
| Sound | Level 4-5 enclosure typical |
| Base tank | Spill containment |
| Exhaust | Directed away |

### Ventilation Calculations
| Air Type | CFM per kW |
|----------|------------|
| Combustion air | 5-10 CFM |
| Cooling air | 200-400 CFM |
| Room ventilation | Based on heat gain |

### Fuel Storage
| Duration | Calculation |
|----------|-------------|
| Consumption | 7 gallons/hour per 100 kW |
| 24 hours | 168 gal per 100 kW |
| 48 hours | 336 gal per 100 kW |
| 96 hours | 672 gal per 100 kW |

---

## Testing and Maintenance

### Testing Schedule
| Test | Frequency | Duration |
|------|-----------|----------|
| No-load exercise | Weekly | 15-30 min |
| Load bank test | Monthly | 30 min |
| Full load test | Annually | 2+ hours |
| Transfer test | Monthly | Full cycle |
| Battery test | Quarterly | Per manufacturer |

### Maintenance Items
| Item | Frequency |
|------|-----------|
| Oil change | 250-500 hours |
| Filter change | 250-500 hours |
| Coolant check | Monthly |
| Belt inspection | Monthly |
| Battery check | Monthly |
| Fuel polishing | Annually |

### Load Bank Testing
| Test Type | Description |
|-----------|-------------|
| Resistive | Real power (kW) |
| Reactive | Simulates motors (kVAR) |
| Combined | Full power factor |
| Building load | Use actual loads |

---

## Paralleling Systems

### Configurations
| Type | Description |
|------|-------------|
| Isolated bus | Separate ATS per generator |
| Paralleled | Multiple generators on bus |
| Utility parallel | Grid interconnection |
| Island | Isolated from utility |

### Paralleling Requirements
| Requirement | Purpose |
|-------------|---------|
| Synchronization | Match frequency, phase, voltage |
| Load sharing | Divide load equally |
| Protection | Fault isolation |
| Reverse power | Prevent motoring |

---

## Redundancy Levels

### Configurations
| Level | Description | Reliability |
|-------|-------------|-------------|
| N | No redundancy | 99.5% |
| N+1 | One spare | 99.9% |
| 2N | Full duplicate | 99.99% |
| 2N+1 | Full + spare | 99.999% |

### Application by Use
| Facility | Minimum |
|----------|---------|
| Standard office | N |
| Hospital | N+1 |
| Data center (Tier II) | N+1 |
| Data center (Tier III) | N+1 concurrent |
| Data center (Tier IV) | 2N |

---

## Cost Factors

### Generator Costs
| Size | Equipment | Installed |
|------|-----------|-----------|
| 50 kW | $20,000 | $50,000 |
| 100 kW | $35,000 | $80,000 |
| 250 kW | $70,000 | $150,000 |
| 500 kW | $120,000 | $250,000 |
| 1000 kW | $200,000 | $400,000 |
| 2000 kW | $350,000 | $700,000 |

### UPS Costs
| Size | Equipment |
|------|-----------|
| 10 kVA | $3,000-5,000 |
| 50 kVA | $15,000-25,000 |
| 100 kVA | $30,000-50,000 |
| 500 kVA | $150,000-250,000 |
| 1000 kVA | $300,000-500,000 |

### Operating Costs
| Item | Annual Cost |
|------|-------------|
| Fuel (testing) | $500-2,000 |
| Maintenance | $2,000-10,000 |
| Testing/inspection | $1,000-3,000 |
| Battery replacement (5-yr) | Per size |

---

## Residential Standby

### Sizing for Homes
| Load | Generator Size |
|------|----------------|
| Essential only | 7.5-12 kW |
| Most circuits | 16-22 kW |
| Whole house | 22-48 kW |

### Essential Loads
| Load | Approximate kW |
|------|----------------|
| Refrigerator | 0.5-1 |
| Sump pump | 0.5-1 |
| Furnace fan | 0.5-1 |
| Well pump | 1-2 |
| A/C (3 ton) | 3-4 |
| A/C (5 ton) | 5-6 |
| Electric range | 8-12 |
| Water heater | 4-5 |
| Pool pump | 1-2 |

### Transfer Options
| Option | Description |
|--------|-------------|
| Manual interlock | Lowest cost, user transfers |
| Automatic essential | Powers critical circuits |
| Automatic whole-house | Powers all circuits |
| Load management | Smart load shedding |

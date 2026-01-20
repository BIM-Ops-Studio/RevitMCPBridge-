# BIM Execution Planning

## BIM Execution Plan (BEP)

### Purpose
Document that defines how BIM will be implemented on a project, including roles, responsibilities, standards, and workflows.

### BEP Components
| Section | Content |
|---------|---------|
| Project information | Name, location, team |
| BIM goals | What BIM will achieve |
| Roles and responsibilities | Who does what |
| Model structure | Organization, files |
| LOD requirements | Level of development |
| Collaboration procedures | File sharing, meetings |
| Quality control | Checking, validation |
| Deliverables | Model, drawings, data |

---

## Level of Development (LOD)

### LOD Definitions (AIA/BIMForum)
| LOD | Description | Use |
|-----|-------------|-----|
| 100 | Conceptual | Massing, area studies |
| 200 | Approximate geometry | Schematic design |
| 300 | Accurate geometry | Design development |
| 350 | Construction-ready | Coordination, detailing |
| 400 | Fabrication | Shop drawings |
| 500 | As-built | Facility management |

### LOD by Phase
| Phase | Typical LOD | Notes |
|-------|-------------|-------|
| Concept | 100 | Massing only |
| Schematic Design | 200 | Generic elements |
| Design Development | 300 | Specific products |
| Construction Docs | 350 | Coordination-ready |
| Construction | 400 | Fabrication data |
| Closeout | 500 | Verified as-built |

### LOD by Element Category
| Category | SD | DD | CD |
|----------|-----|-----|-----|
| Walls | 200 | 300 | 350 |
| Doors | 200 | 300 | 350 |
| Windows | 200 | 300 | 350 |
| Structural | 200 | 300 | 400 |
| MEP | 100 | 300 | 350 |
| FF&E | 100 | 200 | 300 |

### LOD Specifications
| LOD | Geometry | Data | Examples |
|-----|----------|------|----------|
| 100 | Symbol/massing | Area, volume | Room bubble |
| 200 | Generic shape | Approximate size | Generic door |
| 300 | Accurate shape | Specific type | 3'-0" hollow metal |
| 350 | Connections shown | Coordination data | Door with frame detail |
| 400 | Fabrication geometry | Shop drawing data | Door with hardware |
| 500 | Verified geometry | O&M data | As-installed door |

---

## Model Structure

### Model Organization
| Approach | Description | Best For |
|----------|-------------|----------|
| Single model | All disciplines in one | Small projects |
| Linked models | Separate by discipline | Medium projects |
| Federated | Multiple linked, federated | Large projects |
| Cloud-based | Revit Cloud Worksharing | Distributed teams |

### File Naming Convention
```
[Project#]_[Discipline]_[Building/Zone]_[Type].rvt

Examples:
2024-001_A_Central_Model.rvt
2024-001_S_Tower_Model.rvt
2024-001_M_Central_Model.rvt
```

### Discipline Codes
| Code | Discipline |
|------|------------|
| A | Architectural |
| S | Structural |
| M | Mechanical |
| E | Electrical |
| P | Plumbing |
| FP | Fire Protection |
| C | Civil |
| L | Landscape |
| I | Interior |

### Worksets (Architectural)
| Workset | Content |
|---------|---------|
| Shared Levels & Grids | Levels, grids, scope boxes |
| A-Shell | Exterior walls, roof, floors |
| A-Interior | Interior walls, partitions |
| A-Vertical Circulation | Stairs, elevators, ramps |
| A-Core | Core elements |
| A-Ceilings | Ceiling elements |
| A-Casework | Millwork, cabinets |
| A-Furniture | FF&E |
| A-Site | Site elements |
| Linked Models | External references |

---

## Coordination Procedures

### Clash Detection Categories
| Priority | Category | Resolution Time |
|----------|----------|-----------------|
| Critical | Life safety, structural | Immediate |
| Major | MEP vs structure | 1 week |
| Moderate | MEP vs MEP | 2 weeks |
| Minor | Clearance, access | 3 weeks |

### Clash Types
| Type | Example |
|------|---------|
| Hard clash | Duct through beam |
| Soft clash | Insufficient clearance |
| Duplicate | Same element modeled twice |
| Workflow | Model not updated |

### Coordination Meetings
| Meeting | Frequency | Attendees |
|---------|-----------|-----------|
| BIM coordination | Weekly | All disciplines |
| Clash review | Bi-weekly | Design leads |
| Model review | Monthly | Full team + owner |

### Resolution Workflow
```
1. Run clash detection
2. Group and prioritize clashes
3. Assign to responsible party
4. Resolve in model
5. Re-run detection
6. Verify resolution
7. Document in log
```

### Clash Reports
| Content | Format |
|---------|--------|
| Clash image | Screenshot with markup |
| Location | Level, grid intersection |
| Elements involved | ID, category, system |
| Assigned to | Responsible discipline |
| Status | New, active, resolved |
| Resolution | Description of fix |

---

## Quality Control

### Model Checking
| Check Type | Frequency | Tool |
|------------|-----------|------|
| Standards compliance | Weekly | Revit warnings, custom |
| Clash detection | Bi-weekly | Navisworks, BIM 360 |
| Data validation | Monthly | Dynamo, custom |
| Drawing coordination | Per issue | Visual review |

### Revit Warnings
| Warning Type | Action |
|--------------|--------|
| Duplicate instances | Delete duplicates |
| Overlapping elements | Resolve geometry |
| Room separation | Fix boundaries |
| Unjoined walls | Join or intentional |

### Quality Metrics
| Metric | Target |
|--------|--------|
| Open warnings | < 50 per model |
| Unresolved clashes | 0 critical, < 10 major |
| Standards compliance | 100% |
| Model file size | < 300 MB |

### Audit Schedule
| Activity | Frequency |
|----------|-----------|
| Compact central | Weekly |
| Audit model | Monthly |
| Purge unused | Monthly |
| Archive backup | Per milestone |

---

## Data Standards

### Shared Parameters
| Purpose | Location |
|---------|----------|
| Project parameters | Shared parameter file |
| Company standards | Master shared parameters |
| Custom schedules | Defined in template |

### Parameter Naming
```
[Category]_[Property]_[Unit]

Examples:
Room_Finish_Floor
Wall_Fire_Rating_Hours
Door_Hardware_Set
```

### Required Data by LOD
| LOD | Data Requirements |
|-----|-------------------|
| 200 | Type, approximate size |
| 300 | Manufacturer, model, size |
| 350 | All spec data, clearances |
| 400 | Shop drawing data |
| 500 | Asset ID, warranty, O&M |

### Data Drops
| Phase | Data Delivered |
|-------|----------------|
| SD | Areas, volumes, counts |
| DD | Types, sizes, systems |
| CD | Full specifications |
| Construction | Submittals, procurement |
| Closeout | COBie, O&M manuals |

---

## COBie Deliverables

### COBie Overview
| Aspect | Description |
|--------|-------------|
| Purpose | Facility data handover |
| Format | Spreadsheet (Excel) |
| Standard | BS 1192-4 / ISO 19650 |
| Required by | GSA, many owners |

### COBie Worksheets
| Sheet | Content |
|-------|---------|
| Facility | Building information |
| Floor | Levels |
| Space | Rooms |
| Zone | Grouped spaces |
| Type | Product types |
| Component | Individual assets |
| System | Building systems |
| Attribute | Extended data |
| Document | Linked documents |

### COBie Data Sources
| Data | Source |
|------|--------|
| Facility | Project information |
| Spaces | Rooms, areas |
| Types | Families |
| Components | Family instances |
| Attributes | Parameters |

---

## Collaboration Platforms

### Cloud Platforms
| Platform | Features |
|----------|----------|
| BIM 360 / ACC | Autodesk ecosystem, coordination |
| Procore | Project management focus |
| Bluebeam Studio | Markup, review |
| Newforma | Document management |
| PlanGrid | Field access |

### Model Sharing
| Method | Use Case |
|--------|----------|
| Revit Server | Same network |
| BIM 360 Design | Cloud worksharing |
| Linked models | Discipline separation |
| IFC export | Open exchange |

### Communication Protocols
| Type | Platform |
|------|----------|
| RFIs | Procore, BIM 360 |
| Submittals | Procore, Newforma |
| Clash issues | BIM 360, Navisworks |
| Markups | Bluebeam, BIM 360 |

---

## Exchange Formats

### Native Formats
| Format | Use |
|--------|-----|
| RVT | Revit models |
| RFA | Revit families |
| DWG | AutoCAD drawings |
| NWC/NWD | Navisworks |

### Open Formats
| Format | Use |
|--------|-----|
| IFC | Open BIM exchange |
| gbXML | Energy analysis |
| PDF | 2D documentation |
| STEP | Geometry exchange |
| glTF | Visualization |

### IFC Export Settings
| Setting | Recommendation |
|---------|----------------|
| IFC version | IFC4 or IFC2x3 CV2.0 |
| Space boundaries | 2nd level |
| Property sets | Export Revit + IFC |
| Base quantities | Include |

---

## Software Requirements

### Core Applications
| Application | Version | Use |
|-------------|---------|-----|
| Revit | 2024/2025 | Authoring |
| Navisworks | Same year | Coordination |
| BIM 360/ACC | Current | Collaboration |
| AutoCAD | Same year | 2D, detailing |

### Support Applications
| Application | Use |
|-------------|-----|
| Dynamo | Automation |
| Enscape/Lumion | Visualization |
| Bluebeam | Markup |
| Excel | Data management |

### Hardware Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | i7 4-core | i9 8-core |
| RAM | 16 GB | 32-64 GB |
| GPU | 4 GB VRAM | 8+ GB VRAM |
| Storage | SSD 512 GB | NVMe 1 TB |
| Display | 1920×1080 | 2560×1440 |

---

## Training and Support

### Required Training
| Role | Training |
|------|----------|
| BIM Manager | Full platform |
| Modelers | Authoring, standards |
| Coordinators | Clash detection |
| Project managers | Review, access |

### Documentation
| Document | Purpose |
|----------|---------|
| BIM Execution Plan | Project-specific |
| Standards Manual | Company standards |
| Template Guide | Template usage |
| Workflow Guides | Process documentation |

### Support Structure
| Issue | Contact |
|-------|---------|
| Software bugs | Vendor support |
| Standards questions | BIM Manager |
| Model issues | Discipline lead |
| Platform access | IT support |

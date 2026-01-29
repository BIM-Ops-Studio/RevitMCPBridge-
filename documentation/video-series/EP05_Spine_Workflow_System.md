# Episode 5: The Spine Workflow System
## "What if the AI understood entire processes?"

**Duration:** 3:00 (180 seconds)
**Slides:** 14
**Theme:** From discrete commands to intelligent workflows

---

## SLIDE 1: Title Card
**Duration:** 5 seconds
**Visual:** Spine visualization—connected nodes

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    RevitMCPBridge                           │
│                                                             │
│            "Teaching AI to Build"                           │
│                                                             │
│         Episode 5: The Spine Workflow System                │
│                                                             │
│              ●───●───●───●───●───●                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Spine nodes connect in sequence
**Narration:** *[None - music, 5 seconds]*

---

## SLIDE 2: The Limitation
**Duration:** 12 seconds
**Visual:** Individual commands vs workflow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│               THE LIMITATION                                │
│                                                             │
│   705 methods means 705 individual capabilities.            │
│                                                             │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│   │create│ │place │ │add  │ │setup│ │place│ │add  │          │
│   │sheet │ │view  │ │dims │ │sched│ │title│ │notes│          │
│   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │
│                                                             │
│   But a construction document set isn't 705 commands.       │
│                                                             │
│   It's a PROCESS with dependencies, logic, and decisions.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Individual boxes scatter, then question mark appears
**Narration:**
> "Four hundred forty-nine methods. Four hundred forty-nine individual capabilities. But a construction document set isn't four hundred forty-nine separate commands. It's a process. With dependencies. Logic. Decisions. One method at a time wasn't going to cut it."

---

## SLIDE 3: Introducing Spine
**Duration:** 10 seconds
**Visual:** Spine logo/concept

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│                        SPINE                                │
│                                                             │
│              A Workflow Orchestration System                │
│                                                             │
│                                                             │
│        ●─────●─────●─────●─────●─────●─────●                │
│       Profile Resolve Plan Execute Verify Report            │
│                                                             │
│                                                             │
│     "Config-driven. Adaptable. Repeatable. Auditable."      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Spine draws with labels appearing
**Narration:**
> "We built Spine. A workflow orchestration system. Six stages. Profile: understand the project. Resolve: merge standards with specifics. Plan: decide what to create. Execute: make it happen. Verify: check the results. Report: document everything. Config-driven. Adaptable. Repeatable. Auditable."

---

## SLIDE 4: The Architecture
**Duration:** 15 seconds
**Visual:** Spine architecture diagram

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  SPINE ARCHITECTURE                         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   STANDARDS PACK                     │   │
│   │  Sheet naming • View scales • Title blocks • Dims    │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │                                 │
│   ┌───────────────────────▼─────────────────────────────┐   │
│   │                     PROFILE                          │   │
│   │  Project type • Firm standards • Building code       │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │                                 │
│   ┌───────────────────────▼─────────────────────────────┐   │
│   │               RESOLVED CONFIG                        │   │
│   │  "This project, this firm, these sheets, this way"   │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│                    EXECUTION ENGINE                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Flow chart builds top to bottom
**Narration:**
> "At the top: Standards Packs. Sheet naming conventions. View scales. Title block rules. Dimension styles. Below that: Profiles. Project type—single-family, multifamily, commercial. Firm standards. Building code requirements. Merge them together and you get a Resolved Config: exactly what this project needs, done this firm's way."

---

## SLIDE 5: Spine v0.1 - Permit Skeleton
**Duration:** 12 seconds
**Visual:** Permit set output

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              SPINE v0.1: PERMIT SET SKELETON                │
│                                                             │
│   INPUT: A Revit model with rooms, walls, doors, windows    │
│                                                             │
│   OUTPUT:                                                   │
│   ┌───────────────────────────────────────────────────────┐ │
│   │  ✓ A0.01 - COVER SHEET           3D view placed       │ │
│   │  ✓ A0.02 - GENERAL NOTES         Legends placed       │ │
│   │  ✓ A1.01 - FIRST FLOOR PLAN      L1 plan, cropped     │ │
│   │  ✓ A1.02 - SECOND FLOOR PLAN     L2 plan, cropped     │ │
│   │  ✓ A2.01 - ELEVATIONS            4 elevations         │ │
│   │  ✓ A5.01 - BUILDING SECTION      Section views        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│   TIME: Under 3 minutes                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Checkmarks appear one by one
**Narration:**
> "Spine v0.1: Permit Set Skeleton. Give it a model with rooms, walls, doors, windows. It produces a six-sheet permit set. Cover sheet with 3D view. General notes with legends. Floor plans—cropped, scaled, placed. Elevations. Building section. Under three minutes. Every time."

---

## SLIDE 6: Spine v0.2 - Adaptive
**Duration:** 15 seconds
**Visual:** Adaptive workflow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              SPINE v0.2: ADAPTIVE WORKFLOW                  │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  IF project_type == "single_family":                   │ │
│   │      sheets = [A001, A101, A201, A301, A401]          │ │
│   │      scale = "1/4\" = 1'-0\""                          │ │
│   │                                                        │ │
│   │  IF project_type == "multi_family":                    │ │
│   │      sheets = [A001...A010, A101...A115, ...]         │ │
│   │      scale = "1/8\" = 1'-0\""                          │ │
│   │      include_unit_plans = true                         │ │
│   │                                                        │ │
│   │  IF firm == "ARKY":                                    │ │
│   │      title_block = "ARKY - Title Block"                │ │
│   │      numbering = "A-X.XX"                              │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│         "Same engine. Different outputs. Zero manual config."│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Conditional blocks highlight based on narration
**Narration:**
> "Spine v0.2 added intelligence. Adaptive workflows. Single-family home? Here's your sheet list, your scale, your layout. Multi-family? Different sheets, different scale, include unit plans. Working for ARKY? Use their title block, their numbering convention. Same engine. Different outputs. Zero manual configuration."

---

## SLIDE 7: Multi-Firm Support
**Duration:** 12 seconds
**Visual:** Firm profiles

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  MULTI-FIRM SUPPORT                         │
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │    ARKY     │  │  BD Arch    │  │  Custom     │        │
│   │             │  │             │  │             │        │
│   │ A-X.XX nums │  │ A-XXX nums  │  │ Your rules  │        │
│   │ ARKY title  │  │ BD title    │  │ Your title  │        │
│   │ 1/4" scale  │  │ 1/8" scale  │  │ Your scale  │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│   Detection: Automatic based on title block in project      │
│                                                             │
│       "Drop in a project. We know whose standards to use."  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Firm cards appear, detection arrow points to title block
**Narration:**
> "Multi-firm support. Different firms, different standards. ARKY uses A-X-dot-XX numbering. BD Architect uses A-XXX. Detection is automatic—we read the title block in the project and know whose standards to apply. Drop in any project. We know whose rules to follow."

---

## SLIDE 8: The Verification Layer
**Duration:** 12 seconds
**Visual:** Verification checklist

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                 THE VERIFICATION LAYER                      │
│                                                             │
│   After execution, Spine verifies:                          │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  ✓ Sheets created match expected count                 │ │
│   │  ✓ All views placed on correct sheets                  │ │
│   │  ✓ No overlapping viewports                            │ │
│   │  ✓ Title block populated with project info             │ │
│   │  ✓ Scales match standard requirements                  │ │
│   │  ✓ Sheet numbers follow naming convention              │ │
│   │                                                        │ │
│   │  PASS: 6/6 checks passed                               │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│         "Trust, but verify. Automatically."                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Checkmarks verify one by one, PASS badge appears
**Narration:**
> "After every execution, Spine verifies. Sheets created match expected count? Check. Views placed correctly? Check. No overlapping viewports? Check. Title block populated? Scales correct? Naming conventions followed? All checked automatically. Trust, but verify."

---

## SLIDE 9: The Cleanup System
**Duration:** 10 seconds
**Visual:** Cleanup with accounting

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  INTELLIGENT CLEANUP                        │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  WORKFLOW CLEANUP REPORT                               │ │
│   │  ─────────────────────                                 │ │
│   │  Created: 6 sheets, 12 views, 18 viewports             │ │
│   │  Artifacts removed: 3 temp views                       │ │
│   │  Cascade deletions: 0                                  │ │
│   │  Leftovers: 0                                          │ │
│   │                                                        │ │
│   │  Model state: CLEAN                                    │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│      "No orphaned views. No temp elements. Clean model."    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Report generates, CLEAN badge highlights
**Narration:**
> "Spine cleans up after itself. Created six sheets? Tracked. Twelve views? Tracked. Temp views created during workflow? Removed. Orphaned elements? None. Every run ends with a clean model and a complete accounting."

---

## SLIDE 10: Budget Enforcement
**Duration:** 10 seconds
**Visual:** Budget constraints

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  BUDGET ENFORCEMENT                         │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  WORKFLOW CONSTRAINTS                                  │ │
│   │                                                        │ │
│   │  max_steps: 100          Used: 47/100 ✓               │ │
│   │  max_retries: 3          Used: 1/3 ✓                  │ │
│   │  max_undos: 5            Used: 0/5 ✓                  │ │
│   │  max_elapsed: 600s       Used: 127s ✓                 │ │
│   │                                                        │ │
│   │  STATUS: WITHIN BUDGET                                 │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│     "Workflows can't run forever. Guardrails built in."     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Progress bars fill, all green checks
**Narration:**
> "Workflows have budgets. Max steps: one hundred. Max retries: three. Max time: ten minutes. Spine tracks every resource. If something's going wrong—infinite loops, repeated failures—the workflow stops before it causes damage. Guardrails built in."

---

## SLIDE 11: The Portability Test
**Duration:** 12 seconds
**Visual:** Multiple project test results

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                 PORTABILITY PROVEN                          │
│                                                             │
│   Same Spine config. Different projects.                    │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  TEST-4 (2-story residential)     ✓ PASS              │ │
│   │  - 6 sheets, all views placed correctly                │ │
│   │                                                        │ │
│   │  512 Clematis (5-story multifamily) ✓ PASS            │ │
│   │  - 181 doors, 131 windows, handled                     │ │
│   │                                                        │ │
│   │  Avon Park (single-family)        ✓ PASS              │ │
│   │  - Complete CD skeleton in 2:47                        │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│      "Write once. Run on any project."                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Test results check off one by one
**Narration:**
> "We tested portability. Same Spine configuration. Different projects. TEST-4: two-story residential—pass. 512 Clematis: five-story multifamily with a hundred eighty-one doors—pass. Avon Park: single-family—complete CD skeleton in two minutes forty-seven seconds. Write the workflow once. Run it on any project."

---

## SLIDE 12: What This Enables
**Duration:** 10 seconds
**Visual:** Future capabilities

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│               WHAT SPINE ENABLES                            │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                        │ │
│   │  TODAY:                                                │ │
│   │  • Permit set skeletons in minutes                     │ │
│   │  • Automated sheet creation and layout                 │ │
│   │  • Multi-firm standard compliance                      │ │
│   │                                                        │ │
│   │  TOMORROW:                                             │ │
│   │  • Full CD sets from schematic models                  │ │
│   │  • Automated detail generation                         │ │
│   │  • Code compliance checking workflows                  │ │
│   │  • Drawing set coordination                            │ │
│   │                                                        │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Today items appear, then Tomorrow items fade in
**Narration:**
> "What does Spine enable? Today: permit set skeletons in minutes. Automated sheet creation. Multi-firm compliance. Tomorrow: full CD sets from schematic models. Automated detail generation. Code compliance workflows. Drawing coordination across disciplines."

---

## SLIDE 13: The Bigger Picture
**Duration:** 8 seconds
**Visual:** Spine in context

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  THE BIGGER PICTURE                         │
│                                                             │
│                                                             │
│         705 Methods = The vocabulary                        │
│                                                             │
│         Spine = The grammar                                 │
│                                                             │
│         Together = Complete sentences                       │
│                                                             │
│                                                             │
│   "Now Claude doesn't just know words. It speaks fluently." │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Equation builds with emphasis
**Narration:**
> "The bigger picture. Four hundred forty-nine methods—that's vocabulary. Spine—that's grammar. Together? Complete sentences. Now Claude doesn't just know individual commands. It speaks fluent construction documentation."

---

## SLIDE 14: End Card
**Duration:** 6 seconds
**Visual:** Next episode preview

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│                    Next Episode:                            │
│                                                             │
│             "Vision & The Road Ahead"                       │
│                                                             │
│       Level 5: The AI produces 90% of the CD set.           │
│                                                             │
│                                                             │
│                  [BIM Ops Studio]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Fade transition
**Narration:**
> "Final episode: Vision and The Road Ahead. Level 5—where the AI produces ninety percent of the construction document set."

---

## FULL NARRATION SCRIPT

**[INTRO - 5 seconds silence with music]**

Four hundred forty-nine methods. Four hundred forty-nine individual capabilities. But a construction document set isn't four hundred forty-nine separate commands. It's a process. With dependencies. Logic. Decisions. One method at a time wasn't going to cut it.

We built Spine. A workflow orchestration system. Six stages. Profile: understand the project. Resolve: merge standards with specifics. Plan: decide what to create. Execute: make it happen. Verify: check the results. Report: document everything. Config-driven. Adaptable. Repeatable. Auditable.

At the top: Standards Packs. Sheet naming conventions. View scales. Title block rules. Dimension styles. Below that: Profiles. Project type—single-family, multifamily, commercial. Firm standards. Building code requirements. Merge them together and you get a Resolved Config: exactly what this project needs, done this firm's way.

Spine v0.1: Permit Set Skeleton. Give it a model with rooms, walls, doors, windows. It produces a six-sheet permit set. Cover sheet with 3D view. General notes with legends. Floor plans—cropped, scaled, placed. Elevations. Building section. Under three minutes. Every time.

Spine v0.2 added intelligence. Adaptive workflows. Single-family home? Here's your sheet list, your scale, your layout. Multi-family? Different sheets, different scale, include unit plans. Working for ARKY? Use their title block, their numbering convention. Same engine. Different outputs. Zero manual configuration.

Multi-firm support. Different firms, different standards. ARKY uses A-X-dot-XX numbering. BD Architect uses A-XXX. Detection is automatic—we read the title block in the project and know whose standards to apply. Drop in any project. We know whose rules to follow.

After every execution, Spine verifies. Sheets created match expected count? Check. Views placed correctly? Check. No overlapping viewports? Check. Title block populated? Scales correct? Naming conventions followed? All checked automatically. Trust, but verify.

Spine cleans up after itself. Created six sheets? Tracked. Twelve views? Tracked. Temp views created during workflow? Removed. Orphaned elements? None. Every run ends with a clean model and a complete accounting.

Workflows have budgets. Max steps: one hundred. Max retries: three. Max time: ten minutes. Spine tracks every resource. If something's going wrong—infinite loops, repeated failures—the workflow stops before it causes damage. Guardrails built in.

We tested portability. Same Spine configuration. Different projects. TEST-4: two-story residential—pass. 512 Clematis: five-story multifamily with a hundred eighty-one doors—pass. Avon Park: single-family—complete CD skeleton in two minutes forty-seven seconds. Write the workflow once. Run it on any project.

What does Spine enable? Today: permit set skeletons in minutes. Automated sheet creation. Multi-firm compliance. Tomorrow: full CD sets from schematic models. Automated detail generation. Code compliance workflows. Drawing coordination across disciplines.

The bigger picture. Four hundred forty-nine methods—that's vocabulary. Spine—that's grammar. Together? Complete sentences. Now Claude doesn't just know individual commands. It speaks fluent construction documentation.

Final episode: Vision and The Road Ahead. Level 5—where the AI produces ninety percent of the construction document set.

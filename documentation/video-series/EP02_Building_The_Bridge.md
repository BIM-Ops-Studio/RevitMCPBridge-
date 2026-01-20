# Episode 2: Building the Bridge
## "Connecting two worlds that were never meant to talk"

**Duration:** 2:30 (150 seconds)
**Slides:** 12
**Theme:** Technical storytelling—making architecture accessible

---

## SLIDE 1: Title Card
**Duration:** 5 seconds
**Visual:** Two glowing endpoints, connection forming

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    RevitMCPBridge                           │
│                                                             │
│            "Teaching AI to Build"                           │
│                                                             │
│          Episode 2: Building the Bridge                     │
│                                                             │
│                [Connection forming]                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Two dots appear, bridge draws between them
**Narration:** *[None - music, 5 seconds]*

---

## SLIDE 2: The Challenge
**Duration:** 12 seconds
**Visual:** Two software environments, vastly different

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    THE CHALLENGE                            │
│                                                             │
│   ┌──────────────────────┐    ┌──────────────────────┐     │
│   │      CLAUDE          │    │       REVIT          │     │
│   │  ┌────────────────┐  │    │  ┌────────────────┐  │     │
│   │  │ Runs in cloud  │  │    │  │ Runs on desktop│  │     │
│   │  │ Text in/out    │  │    │  │ GUI-based      │  │     │
│   │  │ No file access │  │    │  │ C#/.NET        │  │     │
│   │  │ Stateless      │  │    │  │ Stateful       │  │     │
│   │  └────────────────┘  │    │  └────────────────┘  │     │
│   └──────────────────────┘    └──────────────────────┘     │
│                                                             │
│         "How do you make these talk to each other?"         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Boxes appear, characteristics fade in one by one
**Narration:**
> "Claude runs in the cloud. Revit runs on your desktop. Claude speaks text. Revit speaks geometry. Claude is stateless. Revit holds a massive, complex model in memory. How do you make these talk to each other?"

---

## SLIDE 3: The Key Insight
**Duration:** 10 seconds
**Visual:** MCP protocol visualization

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    THE KEY INSIGHT                          │
│                                                             │
│                Model Context Protocol                       │
│                        (MCP)                                │
│                                                             │
│   ┌─────────┐    JSON    ┌─────────┐    JSON    ┌───────┐  │
│   │ CLAUDE  │ ─────────► │  MCP    │ ─────────► │ TOOL  │  │
│   │         │ ◄───────── │ SERVER  │ ◄───────── │       │  │
│   └─────────┘            └─────────┘            └───────┘  │
│                                                             │
│      "Anthropic built MCP so Claude could use tools.        │
│               We just needed to make Revit... a tool."      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Data flows animate left to right
**Narration:**
> "The insight came from Anthropic themselves. They built MCP—Model Context Protocol—so Claude could use external tools. Database queries. Web searches. File operations. We just needed to make Revit... a tool."

---

## SLIDE 4: The Architecture
**Duration:** 15 seconds
**Visual:** Three-layer architecture diagram

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                 THE ARCHITECTURE                            │
│                                                             │
│   LAYER 1: Claude Code                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  User → "Create a 20x30 room" → Claude Code (WSL)   │   │
│   └─────────────────────────────────────┬───────────────┘   │
│                                         │ stdio             │
│                                         ▼                   │
│   LAYER 2: MCP Server (Python)                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Translates MCP calls → Named Pipe messages         │   │
│   └─────────────────────────────────────┬───────────────┘   │
│                                         │ Named Pipe        │
│                                         ▼                   │
│   LAYER 3: Revit Add-in (C#)                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Receives JSON → Executes Revit API → Returns data  │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Layers appear top-to-bottom, connections draw in
**Narration:**
> "Three layers. At the top: Claude Code running in WSL—Windows Subsystem for Linux. In the middle: a Python MCP server that speaks Claude's language. At the bottom: a C# add-in running inside Revit itself. They communicate through something called a named pipe."

---

## SLIDE 5: Named Pipes
**Duration:** 12 seconds
**Visual:** Pipe visualization with data flowing

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    NAMED PIPES                              │
│                                                             │
│      "A persistent communication channel in Windows"        │
│                                                             │
│                                                             │
│      \\.\pipe\RevitMCPBridge2026                            │
│                                                             │
│    ┌─────────────────────────────────────────────────┐      │
│    │ ═══════════════════════════════════════════════ │      │
│    │  {"method":"createWall","params":{...}}    →    │      │
│    │  {"success":true,"wallId":12345}           ←    │      │
│    │ ═══════════════════════════════════════════════ │      │
│    └─────────────────────────────────────────────────┘      │
│                                                             │
│         Messages flow both directions. Instantly.           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Pipe appears, JSON messages scroll through
**Narration:**
> "Named pipes are a Windows feature. They create a persistent channel between two processes—even if those processes are wildly different. Our pipe is called RevitMCPBridge 2026. JSON commands go in. JSON results come out. Instantly."

---

## SLIDE 6: Inside Revit
**Duration:** 15 seconds
**Visual:** C# add-in architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              INSIDE REVIT: THE ADD-IN                       │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                    MCPServer.cs                        │ │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│   │  │   Listen    │→ │   Parse     │→ │   Route     │    │ │
│   │  │   on Pipe   │  │   JSON      │  │   Method    │    │ │
│   │  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│   │                                           │            │ │
│   │                                           ▼            │ │
│   │  ┌──────────────────────────────────────────────┐     │ │
│   │  │ WallMethods │ ViewMethods │ SheetMethods │...│     │ │
│   │  └──────────────────────────────────────────────┘     │ │
│   │                           │                            │ │
│   │                           ▼                            │ │
│   │                    REVIT API                           │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Request flows through the boxes
**Narration:**
> "Inside Revit, our C# add-in listens on that pipe. When a message arrives, it parses the JSON, identifies the method—create wall, get views, place door—and routes it to the appropriate handler. Each handler talks directly to Revit's API."

---

## SLIDE 7: First Test
**Duration:** 10 seconds
**Visual:** Terminal showing first ping-pong

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  THE FIRST TEST                             │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ $ echo '{"method":"ping"}' | nc -U /pipe/RevitMCP2026 │ │
│   │                                                        │ │
│   │ {"success": true, "result": "pong"}                    │ │
│   │                                                        │ │
│   │ $                                                      │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│              ┌──────────────────────────────┐               │
│              │                              │               │
│              │    IT WORKS.                 │               │
│              │                              │               │
│              └──────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Terminal types out command, response appears
**Narration:**
> "The first test was simple. Send 'ping'. Get 'pong'. We ran the command, held our breath... and there it was. Success: true. Result: pong. Two completely different worlds, talking to each other. It works."

---

## SLIDE 8: The Method Structure
**Duration:** 12 seconds
**Visual:** JSON command anatomy

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                 ANATOMY OF A COMMAND                        │
│                                                             │
│   {                                                         │
│     "method": "createWall",          ← What to do           │
│                                                             │
│     "params": {                      ← How to do it         │
│       "startPoint": [0, 0, 0],          Start coordinate    │
│       "endPoint": [20, 0, 0],           End coordinate      │
│       "levelId": 30,                    Which level         │
│       "height": 10                      Wall height         │
│     }                                                       │
│   }                                                         │
│                                                             │
│        "Plain JSON. Human readable. Machine executable."    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** JSON builds up with annotations appearing
**Narration:**
> "Every command follows the same pattern. Method name—what to do. Parameters—how to do it. StartPoint, endPoint, levelId, height. Plain JSON. Human readable. Machine executable. Claude can construct these commands without special training."

---

## SLIDE 9: The Early Methods
**Duration:** 10 seconds
**Visual:** First methods list

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    FIRST METHODS                            │
│                  November 2024                              │
│                                                             │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                                                       │  │
│   │  ✓ ping              ✓ getLevels                     │  │
│   │  ✓ getProjectInfo    ✓ getWallTypes                  │  │
│   │  ✓ createWall        ✓ getViews                      │  │
│   │  ✓ getElements       ✓ getSheets                     │  │
│   │                                                       │  │
│   │              ~30 methods total                        │  │
│   │                                                       │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                             │
│              "Enough to prove the concept."                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Methods check on one by one
**Narration:**
> "We started with about thirty methods. Ping. GetLevels. CreateWall. GetViews. Basic operations—but enough to prove the concept. Could Claude actually command Revit?"

---

## SLIDE 10: The Revit Context Challenge
**Duration:** 15 seconds
**Visual:** Threading/context visualization

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              THE REVIT CONTEXT CHALLENGE                    │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  REVIT'S RULE: All API calls must happen on         │   │
│   │               Revit's main thread.                   │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   ┌───────────────────────┐                                 │
│   │ External command      │──→ Direct API access ✓          │
│   └───────────────────────┘                                 │
│                                                             │
│   ┌───────────────────────┐                                 │
│   │ Named pipe listener   │──→ Background thread ✗          │
│   │ (different thread)    │                                 │
│   └───────────────────────┘                                 │
│                                                             │
│   SOLUTION: ExternalEvent + IExternalEventHandler           │
│             Queue commands, execute on main thread          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Thread diagram appears, solution highlights
**Narration:**
> "But Revit has rules. All API calls must happen on Revit's main thread. Our pipe listener runs on a background thread. Direct calls would crash. The solution? Revit's External Event system. We queue commands on the background thread, then execute them safely on the main thread. A small detail that took weeks to get right."

---

## SLIDE 11: The Bridge Complete
**Duration:** 8 seconds
**Visual:** Complete architecture, glowing

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              THE BRIDGE: COMPLETE                           │
│                                                             │
│   ┌─────────┐                                    ┌───────┐  │
│   │         │                                    │       │  │
│   │ CLAUDE  │══════════════════════════════════►│ REVIT │  │
│   │         │◄══════════════════════════════════│       │  │
│   │         │                                    │       │  │
│   └─────────┘                                    └───────┘  │
│                                                             │
│      "Natural language in. BIM model changes out."          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  52,400 lines of C# │ 41 source files │ 30 methods  │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Bridge glows, stats appear
**Narration:**
> "And just like that, the bridge was complete. Natural language in. BIM model changes out. Fifty-two thousand lines of C# across forty-one source files. Thirty working methods. It was time to test what this could really do."

---

## SLIDE 12: End Card
**Duration:** 8 seconds
**Visual:** Preview of next episode

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│                    Next Episode:                            │
│                                                             │
│         "First Autonomous Breakthrough"                     │
│                                                             │
│        December 2024: 30 walls appeared.                    │
│           No human touched the mouse.                       │
│                                                             │
│                                                             │
│                  [BIM Ops Studio]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** Fade to next episode preview
**Narration:**
> "Next episode: First Autonomous Breakthrough. December 2024. Thirty walls appeared in Revit. No human touched the mouse."

---

## FULL NARRATION SCRIPT (for recording)

**[INTRO - 5 seconds silence with music]**

Claude runs in the cloud. Revit runs on your desktop. Claude speaks text. Revit speaks geometry. Claude is stateless. Revit holds a massive, complex model in memory. How do you make these talk to each other?

The insight came from Anthropic themselves. They built MCP—Model Context Protocol—so Claude could use external tools. Database queries. Web searches. File operations. We just needed to make Revit... a tool.

Three layers. At the top: Claude Code running in WSL—Windows Subsystem for Linux. In the middle: a Python MCP server that speaks Claude's language. At the bottom: a C# add-in running inside Revit itself. They communicate through something called a named pipe.

Named pipes are a Windows feature. They create a persistent channel between two processes—even if those processes are wildly different. Our pipe is called RevitMCPBridge 2026. JSON commands go in. JSON results come out. Instantly.

Inside Revit, our C# add-in listens on that pipe. When a message arrives, it parses the JSON, identifies the method—create wall, get views, place door—and routes it to the appropriate handler. Each handler talks directly to Revit's API.

The first test was simple. Send 'ping'. Get 'pong'. We ran the command, held our breath... and there it was. Success: true. Result: pong. Two completely different worlds, talking to each other. It works.

Every command follows the same pattern. Method name—what to do. Parameters—how to do it. StartPoint, endPoint, levelId, height. Plain JSON. Human readable. Machine executable. Claude can construct these commands without special training.

We started with about thirty methods. Ping. GetLevels. CreateWall. GetViews. Basic operations—but enough to prove the concept. Could Claude actually command Revit?

But Revit has rules. All API calls must happen on Revit's main thread. Our pipe listener runs on a background thread. Direct calls would crash. The solution? Revit's External Event system. We queue commands on the background thread, then execute them safely on the main thread. A small detail that took weeks to get right.

And just like that, the bridge was complete. Natural language in. BIM model changes out. Fifty-two thousand lines of C# across forty-one source files. Thirty working methods. It was time to test what this could really do.

Next episode: First Autonomous Breakthrough. December 2024. Thirty walls appeared in Revit. No human touched the mouse.

---

## TECHNICAL NOTES

- **Total word count:** ~520 words
- **Speaking pace:** ~200 words/minute = 2:35
- **Key technical terms:** MCP, Named Pipes, ExternalEvent, JSON
- **Tone:** Technical but accessible, building excitement

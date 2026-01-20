# Voice Transcription Corrections

Common misheard words when using Wispr Flow with Claude Code.

## Software Names
| Heard | Actual |
|-------|--------|
| Reddit | Revit |
| Read it | Revit |
| Read | Revit (when in context of architecture) |
| Autodesk | Autodesk (correct) |

## Architecture Terms
| Heard | Actual |
|-------|--------|
| CD | Construction Documents |
| CDs | Construction Documents |
| see the | CD (Construction Documents) |

## Technical Terms
| Heard | Actual |
|-------|--------|
| MCP | MCP (Model Context Protocol) |
| API | API |
| DLL | DLL |

## Context Clues
When the user says:
- "open Reddit" -> They mean "open Revit"
- "Reddit is open" -> "Revit is open"
- "Reddit model" -> "Revit model"
- "in Reddit" -> "in Revit"

## Instructions for Claude
When you see these misheard words in context of:
- BIM/architecture work -> assume Revit
- Construction documents -> assume CD
- Software development -> use exact word

Always clarify if unsure, but default to the corrected term when context is clear.

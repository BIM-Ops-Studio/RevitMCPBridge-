using System.Collections.Generic;

namespace RevitMCPBridge2026.AgentFramework
{
    /// <summary>
    /// Tool definitions that tell Claude what MCP methods are available
    /// These are the "capabilities" the agent has
    /// </summary>
    public static class ToolDefinitions
    {
        /// <summary>
        /// Get all available tool definitions for the agent
        /// Start with most useful tools, expand over time
        /// </summary>
        public static List<ToolDefinition> GetAllTools()
        {
            var tools = new List<ToolDefinition>();

            // UNIVERSAL ACCESS: These tools give access to ALL 437+ MCP methods
            tools.AddRange(GetUniversalTools());

            // FILE OPERATIONS: Read, write, browse files like Claude Code
            tools.AddRange(GetFileTools());

            // MEMORY: Persistent memory across sessions like Claude Code
            tools.AddRange(GetMemoryTools());

            // Add curated tool categories (with descriptions for common tasks)
            tools.AddRange(GetProjectTools());
            tools.AddRange(GetSpatialIntelligenceTools());
            tools.AddRange(GetAnnotationTools());
            tools.AddRange(GetElementTools());
            tools.AddRange(GetViewSheetTools());
            tools.AddRange(GetScheduleTools());

            return tools;
        }

        #region Universal MCP Access Tools

        /// <summary>
        /// Universal tools that give the agent access to ALL MCP methods
        /// </summary>
        public static List<ToolDefinition> GetUniversalTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "listAllMethods",
                    Description = @"List ALL available MCP methods (437+ methods). Use this to discover what methods are available beyond the curated tools.
Categories include: Wall, Door, Window, Room, View, Sheet, Schedule, Family, Parameter, Structural, MEP, Detail, Filter, Material, Phase, Workset, Annotation, and more.
Returns method names grouped by category with descriptions.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            category = new { type = "string", description = "Optional: filter by category (e.g., 'Wall', 'Room', 'Schedule', 'MEP')" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "callMCPMethod",
                    Description = @"Call ANY MCP method by name. Use this when you need a method not in the curated tools list.
First use listAllMethods to discover available methods, then use this to call them.
This is your gateway to all 437+ Revit automation methods.
Common methods: createWall, placeDoor, placeWindow, createRoom, tagRoom, createSchedule, setParameter, etc.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            method = new { type = "string", description = "The MCP method name to call (e.g., 'createWall', 'getRooms', 'batchTagDoors')" },
                            parameters = new { type = "object", description = "Parameters to pass to the method as a JSON object" }
                        },
                        required = new[] { "method" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getMethodInfo",
                    Description = "Get detailed information about a specific MCP method including its parameters, types, and usage examples.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            methodName = new { type = "string", description = "The method name to get info about" }
                        },
                        required = new[] { "methodName" }
                    }
                },
                // Knowledge base tools - load architectural knowledge on demand
                new ToolDefinition
                {
                    Name = "listKnowledgeFiles",
                    Description = @"List all 99 available knowledge files in the knowledge base.
Use this to discover what architectural knowledge is available. Categories include:
- Building Types (17 files): residential, healthcare, office, retail, hospitality, etc.
- Structural/Envelope (12 files): walls, roofs, foundations, glazing
- MEP Systems (10 files): HVAC, electrical, plumbing, fire protection
- Codes/Regulatory (9 files): IBC compliance, egress, accessibility, Florida requirements
- Interior/Finishes (9 files): kitchen/bath design, materials, millwork
- Documentation (7 files): CD standards, annotation, specifications",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getKnowledgeFile",
                    Description = @"Load a specific knowledge file from the knowledge base.
Use when you need detailed information about a specific topic.
Example files:
- 'room-standards.md' - Room sizes by building type
- 'florida-requirements.md' - Florida Building Code specifics
- 'kitchen-bath-design.md' - Kitchen/bath layouts and clearances
- 'code-compliance.md' - IBC occupancy, construction types
- 'egress-design.md' - Exit requirements, travel distance
- 'single-family-residential.md' - House design standards",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            fileName = new { type = "string", description = "Name of the knowledge file (with or without .md extension)" }
                        },
                        required = new[] { "fileName" }
                    }
                }
            };
        }

        #endregion

        #region File Operation Tools

        /// <summary>
        /// File operation tools - read, write, browse files like Claude Code
        /// </summary>
        public static List<ToolDefinition> GetFileTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "readFile",
                    Description = @"Read the contents of a file. Supports text files, code files, JSON, CSV, etc.
Use this to examine project files, scripts, configuration, or any text-based content.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            filePath = new { type = "string", description = "Absolute path to the file to read" },
                            maxLines = new { type = "integer", description = "Maximum lines to read (default: 500)" }
                        },
                        required = new[] { "filePath" }
                    }
                },
                new ToolDefinition
                {
                    Name = "writeFile",
                    Description = @"Write content to a file. Creates the file if it doesn't exist, overwrites if it does.
Use for saving scripts, configurations, reports, or generated content.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            filePath = new { type = "string", description = "Absolute path to the file to write" },
                            content = new { type = "string", description = "Content to write to the file" },
                            append = new { type = "boolean", description = "If true, append instead of overwrite (default: false)" }
                        },
                        required = new[] { "filePath", "content" }
                    }
                },
                new ToolDefinition
                {
                    Name = "listDirectory",
                    Description = @"List files and folders in a directory.
Use to explore the file system, find project files, or browse directories.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            path = new { type = "string", description = "Directory path to list" },
                            pattern = new { type = "string", description = "Optional filter pattern (e.g., '*.rvt', '*.pdf')" },
                            recursive = new { type = "boolean", description = "Include subdirectories (default: false)" }
                        },
                        required = new[] { "path" }
                    }
                },
                new ToolDefinition
                {
                    Name = "searchFiles",
                    Description = @"Search for files by name pattern across directories.
Use to find specific files like Revit models, PDFs, or scripts.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            startPath = new { type = "string", description = "Directory to start searching from" },
                            pattern = new { type = "string", description = "File name pattern (e.g., '*.rvt', '*floor*.pdf')" },
                            maxResults = new { type = "integer", description = "Maximum results to return (default: 50)" }
                        },
                        required = new[] { "startPath", "pattern" }
                    }
                },
                new ToolDefinition
                {
                    Name = "fileInfo",
                    Description = "Get detailed information about a file (size, dates, attributes).",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            filePath = new { type = "string", description = "Path to the file" }
                        },
                        required = new[] { "filePath" }
                    }
                },
                new ToolDefinition
                {
                    Name = "copyFile",
                    Description = "Copy a file from one location to another.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            sourcePath = new { type = "string", description = "Source file path" },
                            destinationPath = new { type = "string", description = "Destination file path" },
                            overwrite = new { type = "boolean", description = "Overwrite if exists (default: false)" }
                        },
                        required = new[] { "sourcePath", "destinationPath" }
                    }
                },
                new ToolDefinition
                {
                    Name = "deleteFile",
                    Description = "Delete a file. Use with caution.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            filePath = new { type = "string", description = "Path to the file to delete" }
                        },
                        required = new[] { "filePath" }
                    }
                },
                new ToolDefinition
                {
                    Name = "createDirectory",
                    Description = "Create a new directory (folder).",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            path = new { type = "string", description = "Path for the new directory" }
                        },
                        required = new[] { "path" }
                    }
                }
            };
        }

        #endregion

        #region Memory Tools

        /// <summary>
        /// Memory tools - persistent memory across sessions like Claude Code
        /// Stored locally in JSON for Phase 1, can connect to Memory MCP later
        /// </summary>
        public static List<ToolDefinition> GetMemoryTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "memoryStore",
                    Description = @"Store a memory for future sessions. Use this to remember:
- Important decisions made during this session
- User preferences and corrections
- Project-specific information learned
- Errors encountered and how they were solved
- Useful patterns discovered",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            content = new { type = "string", description = "The memory content to store" },
                            memoryType = new { type = "string", description = "Type: decision, fact, preference, context, outcome, error, correction" },
                            project = new { type = "string", description = "Optional project name this relates to" },
                            importance = new { type = "integer", description = "Importance 1-10 (10=critical, default=5)" },
                            tags = new { type = "array", description = "Optional tags for categorization" }
                        },
                        required = new[] { "content" }
                    }
                },
                new ToolDefinition
                {
                    Name = "memoryRecall",
                    Description = @"Search memories by text query. Use this to recall:
- Previous decisions or preferences
- How issues were resolved before
- Project-specific context
- User corrections",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            query = new { type = "string", description = "Search query to find relevant memories" },
                            project = new { type = "string", description = "Optional: filter by project name" },
                            memoryType = new { type = "string", description = "Optional: filter by type" },
                            limit = new { type = "integer", description = "Max results to return (default: 10)" }
                        },
                        required = new[] { "query" }
                    }
                },
                new ToolDefinition
                {
                    Name = "memoryGetContext",
                    Description = @"Get relevant context for the current session. Call at session start.
Returns recent high-importance memories, corrections, and project context.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            project = new { type = "string", description = "Optional project name to focus on" },
                            includeCorrections = new { type = "boolean", description = "Include corrections (default: true)" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "memoryStoreCorrection",
                    Description = @"Store a correction when you made a mistake. HIGH PRIORITY.
These are loaded at session start to prevent repeating mistakes.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            whatISaid = new { type = "string", description = "What you incorrectly stated or did" },
                            whatWasWrong = new { type = "string", description = "Why it was wrong" },
                            correctApproach = new { type = "string", description = "The right way to handle this" },
                            project = new { type = "string", description = "Optional project name" },
                            category = new { type = "string", description = "Category: code, architecture, workflow, preferences" }
                        },
                        required = new[] { "whatISaid", "whatWasWrong", "correctApproach" }
                    }
                },
                new ToolDefinition
                {
                    Name = "memoryGetCorrections",
                    Description = "Get stored corrections to review past mistakes and learnings.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            project = new { type = "string", description = "Optional: filter by project" },
                            limit = new { type = "integer", description = "Max results (default: 10)" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "memorySummarizeSession",
                    Description = @"Summarize a work session. Call at end of significant sessions.
Captures key outcomes, decisions, problems solved, and next steps.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            project = new { type = "string", description = "Project name" },
                            summary = new { type = "string", description = "Brief overall summary" },
                            keyOutcomes = new { type = "array", description = "List of main things achieved" },
                            decisionsMade = new { type = "array", description = "Important decisions and reasoning" },
                            problemsSolved = new { type = "array", description = "Issues encountered and solutions" },
                            openQuestions = new { type = "array", description = "Unresolved questions" },
                            nextSteps = new { type = "array", description = "Concrete next actions" }
                        },
                        required = new[] { "project", "summary" }
                    }
                },
                new ToolDefinition
                {
                    Name = "memoryStats",
                    Description = "Get statistics about stored memories.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                }
            };
        }

        #endregion

        #region Project Tools

        public static List<ToolDefinition> GetProjectTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getProjectInfo",
                    Description = "Get information about the current Revit project including name, number, address, client, and file path.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getLevels",
                    Description = "Get all levels in the project with their names and elevations.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getActiveView",
                    Description = "Get information about the currently active view in Revit.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                }
            };
        }

        #endregion

        #region Spatial Intelligence Tools

        public static List<ToolDefinition> GetSpatialIntelligenceTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getElementBoundingBox",
                    Description = "Get the bounding box (min/max coordinates, width, height, center) of any element.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            elementId = new { type = "integer", description = "The element ID to get bounds for" }
                        },
                        required = new[] { "elementId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getViewportBoundingBoxes",
                    Description = "Get all viewports on a sheet with their positions and bounds. Essential for understanding sheet layout.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            sheetId = new { type = "integer", description = "The sheet element ID" }
                        },
                        required = new[] { "sheetId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getAnnotationBoundingBoxes",
                    Description = "Get all annotations in a view with their bounding boxes. Use this to understand what annotations exist and where.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "The view element ID" }
                        },
                        required = new[] { "viewId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getSheetLayout",
                    Description = "Get complete sheet layout including title block, viewports, annotations, and logical zones. This is the master method for understanding sheet organization.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            sheetId = new { type = "integer", description = "The sheet element ID" }
                        },
                        required = new[] { "sheetId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "findEmptySpaceOnSheet",
                    Description = "Find empty rectangular spaces on a sheet where annotations can be placed without overlapping existing content.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            sheetId = new { type = "integer", description = "The sheet element ID" },
                            requiredWidth = new { type = "number", description = "Required width in feet (default 0.5 = 6 inches)" },
                            requiredHeight = new { type = "number", description = "Required height in feet (default 0.25 = 3 inches)" },
                            preferredZone = new { type = "string", description = "Preferred zone: notesArea, legendArea, drawingArea, or any" }
                        },
                        required = new[] { "sheetId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "checkForOverlaps",
                    Description = "Check if placing an element at a proposed location would overlap with existing annotations. Use BEFORE placing to avoid conflicts.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "The view element ID" },
                            x = new { type = "number", description = "Proposed X coordinate" },
                            y = new { type = "number", description = "Proposed Y coordinate" },
                            width = new { type = "number", description = "Width of element to place" },
                            height = new { type = "number", description = "Height of element to place" }
                        },
                        required = new[] { "viewId", "x", "y" }
                    }
                },
                new ToolDefinition
                {
                    Name = "suggestPlacementLocation",
                    Description = "Get AI-suggested optimal placement location for an annotation near a target element, avoiding overlaps.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            targetElementId = new { type = "integer", description = "Element ID to place annotation near" },
                            viewId = new { type = "integer", description = "View ID (optional, uses active view if not specified)" },
                            annotationWidth = new { type = "number", description = "Width of annotation to place" },
                            annotationHeight = new { type = "number", description = "Height of annotation to place" }
                        },
                        required = new[] { "targetElementId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "autoArrangeAnnotations",
                    Description = "Automatically arrange a group of annotations in a column or row with equal spacing. Great for organizing keynote legends.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            elementIds = new { type = "array", items = new { type = "integer" }, description = "Array of element IDs to arrange" },
                            arrangement = new { type = "string", description = "column or row" },
                            spacing = new { type = "number", description = "Spacing between elements in feet (default 0.08 = ~1 inch)" },
                            startX = new { type = "number", description = "Starting X coordinate" },
                            startY = new { type = "number", description = "Starting Y coordinate" },
                            alignment = new { type = "string", description = "For columns: left, center, right. For rows: top, center, bottom" }
                        },
                        required = new[] { "elementIds" }
                    }
                },
                new ToolDefinition
                {
                    Name = "placeAnnotationInZone",
                    Description = "Place an annotation in a logical zone (topLeft, topRight, bottomLeft, bottomRight, center) with automatic collision avoidance.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "View ID to place in" },
                            zone = new { type = "string", description = "Zone: topLeft, topRight, bottomLeft, bottomRight, center" },
                            annotationType = new { type = "string", description = "Type: text, keynote, generic" },
                            content = new { type = "string", description = "Text content (for text type)" },
                            typeId = new { type = "integer", description = "Type ID for keynote or generic annotation" }
                        },
                        required = new[] { "viewId", "zone" }
                    }
                },
                new ToolDefinition
                {
                    Name = "placeRelativeTo",
                    Description = "Place an annotation relative to another element (above, below, left, right) with specified offset.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            referenceElementId = new { type = "integer", description = "Element ID to place relative to" },
                            position = new { type = "string", description = "Position: above, below, left, right" },
                            offset = new { type = "number", description = "Distance from reference element in feet" },
                            annotationType = new { type = "string", description = "Type: text, generic" },
                            content = new { type = "string", description = "Text content" },
                            typeId = new { type = "integer", description = "Type ID for annotation" }
                        },
                        required = new[] { "referenceElementId", "position" }
                    }
                }
            };
        }

        #endregion

        #region Annotation Tools

        public static List<ToolDefinition> GetAnnotationTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getTextNotes",
                    Description = "Get all text notes in the active view or a specified view.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "View ID (optional, uses active view if not specified)" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "createTextNote",
                    Description = "Create a text note at a specified location.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            text = new { type = "string", description = "The text content" },
                            x = new { type = "number", description = "X coordinate" },
                            y = new { type = "number", description = "Y coordinate" },
                            viewId = new { type = "integer", description = "View ID (optional)" },
                            typeId = new { type = "integer", description = "Text note type ID (optional)" }
                        },
                        required = new[] { "text", "x", "y" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getGenericAnnotationTypes",
                    Description = "Get all available generic annotation family types (including keynotes).",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "placeGenericAnnotation",
                    Description = "Place a generic annotation family instance at a location.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            typeId = new { type = "integer", description = "The family type ID" },
                            x = new { type = "number", description = "X coordinate" },
                            y = new { type = "number", description = "Y coordinate" },
                            viewId = new { type = "integer", description = "View ID (optional)" }
                        },
                        required = new[] { "typeId", "x", "y" }
                    }
                },
                new ToolDefinition
                {
                    Name = "placeKeynote",
                    Description = "Place a keynote annotation. Use this for keynote legends and plan keynotes.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            typeId = new { type = "integer", description = "Keynote type ID" },
                            x = new { type = "number", description = "X coordinate" },
                            y = new { type = "number", description = "Y coordinate" },
                            viewId = new { type = "integer", description = "View ID (optional)" }
                        },
                        required = new[] { "typeId", "x", "y" }
                    }
                },
                new ToolDefinition
                {
                    Name = "modifyTextNote",
                    Description = "Modify an existing text note's content or position.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            elementId = new { type = "integer", description = "Text note element ID" },
                            newText = new { type = "string", description = "New text content" },
                            newX = new { type = "number", description = "New X position" },
                            newY = new { type = "number", description = "New Y position" }
                        },
                        required = new[] { "elementId" }
                    }
                }
            };
        }

        #endregion

        #region Element Tools

        public static List<ToolDefinition> GetElementTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getWalls",
                    Description = "Get all walls in the model or on a specific level.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            levelId = new { type = "integer", description = "Filter by level ID (optional)" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getDoors",
                    Description = "Get all doors in the model with their properties.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getWindows",
                    Description = "Get all windows in the model with their properties.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getRooms",
                    Description = "Get all rooms in the model with their names, numbers, and areas.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "deleteElements",
                    Description = "Delete one or more elements by their IDs. Use with caution.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            elementIds = new { type = "array", items = new { type = "integer" }, description = "Array of element IDs to delete" }
                        },
                        required = new[] { "elementIds" }
                    }
                },
                new ToolDefinition
                {
                    Name = "getElementById",
                    Description = "Get detailed information about a specific element by its ID.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            elementId = new { type = "integer", description = "The element ID" }
                        },
                        required = new[] { "elementId" }
                    }
                }
            };
        }

        #endregion

        #region View and Sheet Tools

        public static List<ToolDefinition> GetViewSheetTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getSheets",
                    Description = "Get all sheets in the project with their numbers and names.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getViews",
                    Description = "Get all views in the project, optionally filtered by type.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewType = new { type = "string", description = "Filter by type: FloorPlan, CeilingPlan, Elevation, Section, ThreeD, Legend, Schedule, Sheet" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "setActiveView",
                    Description = "Switch to a specific view or sheet by ID. Opens the view in Revit.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "View or sheet ID to activate" }
                        },
                        required = new[] { "viewId" }
                    }
                },
                new ToolDefinition
                {
                    Name = "captureViewport",
                    Description = "Capture a screenshot of the current or specified view.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "View ID (optional, uses active view)" },
                            width = new { type = "integer", description = "Image width in pixels" },
                            height = new { type = "integer", description = "Image height in pixels" }
                        },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "analyzeView",
                    Description = "VISUAL VERIFICATION: Capture the current view/sheet and analyze it with AI vision. Use this to SEE what you've done and verify it worked correctly. Call this after placing elements to confirm they appear correctly.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            viewId = new { type = "integer", description = "View or sheet ID to analyze (optional, uses active view)" },
                            question = new { type = "string", description = "What to look for or verify (e.g., 'Are the viewports placed correctly?', 'Is the drafting view visible on the sheet?')" }
                        },
                        required = new[] { "question" }
                    }
                },
                new ToolDefinition
                {
                    Name = "placeMultipleViewsOnSheet",
                    Description = "BATCH PLACEMENT: Place multiple views on a sheet with AUTOMATIC GRID LAYOUT. Views are arranged in a grid pattern to AVOID OVERLAPPING. USE THIS instead of calling placeViewOnSheet multiple times! Supports intelligent layout presets.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            sheetId = new { type = "integer", description = "Target sheet ID" },
                            viewIds = new {
                                type = "array",
                                items = new { type = "integer" },
                                description = "Array of view IDs to place on the sheet"
                            },
                            layout = new {
                                type = "string",
                                description = "Layout preset: 'auto' (smart detection), 'row' (horizontal), 'column' (vertical), 'grid-2x2', 'grid-2x3', 'grid-3x2', 'grid-3x3', 'grid-4x3', 'left-column', 'right-column', 'top-row', 'bottom-row'. Default: 'auto'"
                            },
                            columns = new { type = "integer", description = "Override number of columns (optional)" },
                            margin = new { type = "number", description = "Space between viewports in feet (default: 0.08 = ~1 inch)" }
                        },
                        required = new[] { "sheetId", "viewIds" }
                    }
                }
            };
        }

        #endregion

        #region Schedule Tools

        public static List<ToolDefinition> GetScheduleTools()
        {
            return new List<ToolDefinition>
            {
                new ToolDefinition
                {
                    Name = "getSchedules",
                    Description = "Get all schedules in the project.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new { },
                        required = new string[] { }
                    }
                },
                new ToolDefinition
                {
                    Name = "getScheduleData",
                    Description = "Get the data (rows and columns) from a specific schedule.",
                    InputSchema = new
                    {
                        type = "object",
                        properties = new
                        {
                            scheduleId = new { type = "integer", description = "Schedule element ID" }
                        },
                        required = new[] { "scheduleId" }
                    }
                }
            };
        }

        #endregion
    }
}

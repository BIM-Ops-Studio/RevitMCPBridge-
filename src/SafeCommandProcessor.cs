using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Autodesk.Revit.UI;
using Autodesk.Revit.DB;

namespace RevitMCPBridge
{
    /// <summary>
    /// SafeCommandProcessor: Multi-layer intelligence system for processing natural language commands.
    /// Provides guardrails against hallucination, unclear input, and unsafe operations.
    /// </summary>
    public class SafeCommandProcessor
    {
        #region Enums and Classes

        public enum UserIntent
        {
            Create,      // make, create, add, new, put, place
            Find,        // show, find, where, get, open, display
            Modify,      // change, update, move, edit, fix, adjust
            Delete,      // remove, delete, get rid of, clear
            Question,    // what, how, why, is, can, does, tell me
            List,        // list, show all, get all
            Unknown      // Ask for clarification
        }

        public class ExtractedEntities
        {
            public string ElementType { get; set; }      // sheet, door, wall, room, etc.
            public string Name { get; set; }             // A-101, "Master Bedroom"
            public string Location { get; set; }         // ground floor, north wall
            public string Size { get; set; }             // 3x5, 10 feet
            public string AdditionalContext { get; set; } // any other relevant info
            public double Confidence { get; set; }       // 0.0 - 1.0
        }

        public class ProcessedCommand
        {
            public bool Success { get; set; }
            public string Method { get; set; }           // MCP method name
            public JObject Parameters { get; set; }      // Method parameters
            public string Description { get; set; }      // Human-readable description
            public int AffectedCount { get; set; }       // Number of elements affected
            public bool RequiresConfirmation { get; set; }
            public string ClarificationNeeded { get; set; } // Question to ask user
            public double Confidence { get; set; }
            public UserIntent Intent { get; set; }       // Classified intent
            public ExtractedEntities Entities { get; set; } // Extracted entities
        }

        public class ConversationContext
        {
            public UserIntent LastIntent { get; set; }
            public ExtractedEntities LastEntities { get; set; }
            public string LastMethod { get; set; }
            public string PendingQuestion { get; set; }
            public DateTime LastInteraction { get; set; }

            // Hybrid system: Store preferences from conversation for use in subsequent commands
            public int? PreferredRangeStart { get; set; }    // e.g., 200 from "in the 200s"
            public string PreferredDiscipline { get; set; }  // e.g., "A" from "A sheets"
            public int? PreferredCount { get; set; }         // e.g., 5 from "five sheets"
            public string PreferredSheetType { get; set; }   // e.g., "DETAILS" from "detail sheets"

            // Context expiry - preferences are valid for 2 minutes
            public DateTime PreferencesSetAt { get; set; }
            public bool HasValidPreferences => PreferredRangeStart.HasValue &&
                                               (DateTime.Now - PreferencesSetAt).TotalMinutes < 2;

            public void ClearPreferences()
            {
                PreferredRangeStart = null;
                PreferredDiscipline = null;
                PreferredCount = null;
                PreferredSheetType = null;
            }
        }

        #endregion

        #region Private Fields

        private UIApplication _uiApp;
        private readonly Dictionary<string, string> _corrections;
        private readonly Dictionary<string, string[]> _elementPatterns;
        private readonly Dictionary<string, string[]> _intentPatterns;
        private readonly HashSet<string> _validMcpMethods;
        private readonly Dictionary<string, string[]> _methodRequirements;
        private readonly string _ollamaEndpoint = "http://localhost:11434/api/generate";
        private string _localModel = "llama3.1:8b-instruct-q4_0";  // Instruction-tuned model that works on CPU
        private ConversationContext _context;
        private static readonly HttpClient _httpClient;
        private string _injectedKnowledge = "";

        // Static constructor to configure HttpClient once
        static SafeCommandProcessor()
        {
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(60);
        }

        #endregion

        #region Constructor

        public SafeCommandProcessor(UIApplication uiApp)
        {
            _uiApp = uiApp;
            _context = new ConversationContext();

            // Initialize corrections dictionary (typos to correct words)
            _corrections = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                // Common typos
                {"shet", "sheet"}, {"shee", "sheet"}, {"shit", "sheet"},
                {"foor", "floor"}, {"flor", "floor"}, {"floorplan", "floor plan"},
                {"dor", "door"}, {"dooor", "door"},
                {"windo", "window"}, {"windw", "window"},
                {"wal", "wall"}, {"waal", "wall"},
                {"rom", "room"}, {"roo", "room"}, {"rooom", "room"},
                {"batroom", "bathroom"}, {"bathrom", "bathroom"},
                {"kichen", "kitchen"}, {"kitchn", "kitchen"},
                {"bedroo", "bedroom"}, {"bedrom", "bedroom"},
                {"crete", "create"}, {"creat", "create"}, {"craete", "create"},
                {"mak", "make"}, {"mke", "make"},
                {"plac", "place"}, {"palce", "place"},
                {"delet", "delete"}, {"remov", "remove"},
                {"updat", "update"}, {"chang", "change"},
                {"viwe", "view"}, {"veiw", "view"},
                {"scedule", "schedule"}, {"shedule", "schedule"},
                {"dimenson", "dimension"}, {"dimention", "dimension"},
                {"anottation", "annotation"}, {"anotation", "annotation"},
                {"elevetion", "elevation"}, {"elevtion", "elevation"},
                {"secton", "section"}, {"seciton", "section"},
                {"titel", "title"}, {"tittle", "title"},
                {"paramter", "parameter"}, {"paramater", "parameter"},
                // Voice transcription errors
                {"reddit", "revit"}, {"read it", "revit"},
                {"see the", "cd"}, {"cd", "construction documents"},
            };

            // Element type patterns (canonical name -> variations)
            // IMPORTANT: More specific patterns must come FIRST to avoid false matches
            // e.g., "detail view" before "view", "floor plan" before "floor"
            _elementPatterns = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
            {
                // Multi-word patterns FIRST (most specific)
                {"detail view", new[] {"detail view", "drafting view", "drafting detail", "detail views", "drafting views", "drafting details"}},
                {"floor plan", new[] {"floor plan", "floorplan"}},
                {"title block", new[] {"title block", "titleblock", "border"}},
                {"text note", new[] {"text note", "textnote"}},
                // Then single-word patterns
                {"sheet", new[] {"sheet", "sheets", "drawing", "document"}},
                {"door", new[] {"door", "doors", "entry", "entrance", "opening"}},
                {"window", new[] {"window", "windows", "glazing", "glass"}},
                {"wall", new[] {"wall", "walls", "partition", "barrier"}},
                {"room", new[] {"room", "rooms", "space", "area"}},
                {"elevation", new[] {"elevation", "elevations", "facade", "exterior view"}},
                {"section", new[] {"section", "sections", "cut", "cross section"}},
                {"schedule", new[] {"schedule", "schedules", "table", "list"}},
                {"dimension", new[] {"dimension", "dimensions", "measurement", "size"}},
                {"tag", new[] {"tag", "tags", "label", "marker"}},
                {"level", new[] {"level", "levels", "story"}},
                {"ceiling", new[] {"ceiling", "ceilings", "soffit"}},
                {"roof", new[] {"roof", "roofs", "roofing"}},
                {"stair", new[] {"stair", "stairs", "staircase", "steps"}},
                {"railing", new[] {"railing", "railings", "guardrail", "handrail"}},
                {"column", new[] {"column", "columns", "pillar", "post"}},
                {"beam", new[] {"beam", "beams", "girder", "header"}},
                {"furniture", new[] {"furniture", "desk", "chair", "table", "sofa", "bed"}},
                {"fixture", new[] {"fixture", "fixtures", "toilet", "sink", "tub", "shower"}},
                {"cabinet", new[] {"cabinet", "cabinets", "casework", "counter"}},
                {"viewport", new[] {"viewport", "viewports", "view port"}},
                {"detail", new[] {"detail", "details"}},
                {"view", new[] {"view", "views"}},
                {"plan", new[] {"plan", "layout"}},
                {"floor", new[] {"floor"}},
                {"note", new[] {"note", "notes", "annotation", "label"}},
                {"text", new[] {"text"}},
            };

            // Intent patterns
            _intentPatterns = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
            {
                {"Create", new[] {"make", "create", "add", "new", "put", "place", "insert", "draw", "build"}},
                {"Find", new[] {"show", "find", "where", "get", "open", "display", "see", "look", "view", "go to"}},
                {"Modify", new[] {"change", "update", "move", "edit", "fix", "adjust", "modify", "set", "rename"}},
                {"Delete", new[] {"remove", "delete", "get rid", "clear", "erase", "destroy"}},
                {"Question", new[] {"what", "how", "why", "is", "can", "does", "tell me", "explain", "which"}},
                {"List", new[] {"list", "show all", "get all", "display all", "enumerate"}},
            };

            // Valid MCP methods (all 437 methods)
            _validMcpMethods = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                // Sheets
                "createSheet", "getSheets", "deleteSheet", "renameSheet", "placeViewOnSheet",
                "getViewportsOnSheet", "moveViewportOnSheet", "removeViewportFromSheet",
                "setSheetParameter", "getSheetParameter", "duplicateSheet",

                // Views
                "getViews", "createFloorPlan", "createCeilingPlan", "createElevation",
                "createSection", "create3DView", "duplicateView", "deleteView",
                "setViewScale", "setViewCropBox", "zoomToFit", "zoomToElement", "showElement",

                // Walls
                "createWall", "createWalls", "getWalls", "deleteWall", "modifyWall",
                "setWallParameter", "getWallTypes", "splitWall", "joinWalls",
                "getWallLocationCurve", "changeWallType",

                // Doors & Windows
                "placeDoor", "placeWindow", "getDoors", "getWindows",
                "deleteDoor", "deleteWindow", "getDoorTypes", "getWindowTypes",
                "setDoorParameter", "setWindowParameter", "swingDoor", "flipWindow",

                // Rooms
                "createRoom", "getRooms", "deleteRoom", "tagRoom", "getRoomBoundaries",
                "setRoomParameter", "getRoomArea", "getRoomVolume", "createRoomSeparationLine",

                // Text & Annotations
                "placeTextNote", "getTextNotes", "deleteTextNote", "updateTextNote",
                "placeTag", "placeDimension", "placeKeynote", "getTextNoteTypes",

                // Schedules
                "createSchedule", "getSchedules", "deleteSchedule", "addScheduleField",
                "removeScheduleField", "setScheduleFilter", "getScheduleData", "exportSchedule",

                // Families
                "loadFamily", "getLoadedFamilies", "placeFamilyInstance", "getFamilyTypes",
                "deleteFamilyInstance", "setFamilyParameter", "getFamilyParameter",

                // Levels & Grids
                "getLevels", "createLevel", "deleteLevel", "getGrids", "createGrid",

                // Materials
                "getMaterials", "createMaterial", "setMaterialParameter", "applyMaterial",

                // General
                "getElements", "getElementsByCategory", "deleteElements", "getElementLocation",
                "setElementParameter", "getElementParameter", "getCategories",
                "getProjectInfo", "setProjectInfo", "getActiveView", "setActiveView",
                "undo", "redo", "save", "exportToPDF", "exportToImage",
            };

            // Method requirements (what parameters are required/optional)
            _methodRequirements = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
            {
                {"createSheet", new[] {"sheetNumber"}},
                {"placeViewOnSheet", new[] {"sheetId", "viewId"}},
                {"createWall", new[] {"startPoint", "endPoint"}},
                {"placeDoor", new[] {"wallId", "location"}},
                {"placeWindow", new[] {"wallId", "location"}},
                {"placeTextNote", new[] {"text", "x", "y"}},
                {"createRoom", new[] {"levelId", "point"}},
                {"placeFamilyInstance", new[] {"familyName", "typeName", "location"}},
            };
        }

        /// <summary>
        /// Parameterless constructor for use without direct Revit access.
        /// </summary>
        public SafeCommandProcessor() : this(null)
        {
        }

        #endregion

        #region Public Methods

        /// <summary>
        /// Inject domain knowledge context for the LLM to use.
        /// This prevents hallucination by giving the LLM accurate reference information.
        /// </summary>
        public void InjectKnowledge(string knowledge)
        {
            _injectedKnowledge = knowledge ?? "";
        }

        /// <summary>
        /// Clear injected knowledge.
        /// </summary>
        public void ClearKnowledge()
        {
            _injectedKnowledge = "";
        }

        /// <summary>
        /// Set the local Ollama model to use.
        /// Call this after detecting which models are available.
        /// </summary>
        public void SetLocalModel(string modelName)
        {
            if (!string.IsNullOrEmpty(modelName))
            {
                _localModel = modelName;
            }
        }

        /// <summary>
        /// Get the current local model name.
        /// </summary>
        public string GetLocalModel()
        {
            return _localModel;
        }

        /// <summary>
        /// Get current conversation context.
        /// </summary>
        public ConversationContext GetContext()
        {
            return _context;
        }

        /// <summary>
        /// Reset conversation context.
        /// </summary>
        public void ResetContext()
        {
            _context = new ConversationContext();
        }

        #endregion

        #region Main Processing Method

        /// <summary>
        /// Main entry point for processing user input with all safety layers.
        /// </summary>
        public async Task<ProcessedCommand> ProcessInputAsync(string rawInput)
        {
            try
            {
                // Layer 1: Clean and correct input
                string cleanedInput = CleanInput(rawInput);
                string lower = cleanedInput.ToLower();

                // =============================================================================
                // NATURAL LANGUAGE SHORTCUTS - Handle common commands without needing the LLM
                // These patterns recognize many natural ways of speaking
                // =============================================================================

                // Helper to extract sheet number from input
                string ExtractSheetNumber(string input)
                {
                    var match = Regex.Match(input, @"[A-Z]+-?\d+(?:[\.\-]\d+)*", RegexOptions.IgnoreCase);
                    return match.Success ? match.Value.ToUpper().TrimEnd('.', ',', '!', '?') : "";
                }

                // Helper to extract a name in quotes
                string ExtractQuotedName(string input)
                {
                    var match = Regex.Match(input, @"""([^""]+)""|'([^']+)'");
                    return match.Success ? (match.Groups[1].Value ?? match.Groups[2].Value) : "";
                }

                // Helper to extract quantity (number words or digits)
                int ExtractQuantity(string input)
                {
                    // Check for number words first
                    var wordToNum = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase)
                    {
                        {"one", 1}, {"two", 2}, {"three", 3}, {"four", 4}, {"five", 5},
                        {"six", 6}, {"seven", 7}, {"eight", 8}, {"nine", 9}, {"ten", 10},
                        {"eleven", 11}, {"twelve", 12}, {"fifteen", 15}, {"twenty", 20},
                        {"a few", 3}, {"some", 5}, {"several", 5}, {"couple", 2}, {"a couple", 2}
                    };

                    foreach (var kvp in wordToNum)
                    {
                        if (Regex.IsMatch(input, $@"\b{Regex.Escape(kvp.Key)}\b", RegexOptions.IgnoreCase))
                            return kvp.Value;
                    }

                    // Check for digits (but not sheet numbers like A-601)
                    var digitMatch = Regex.Match(input, @"(?<![A-Z]-?)(\d{1,2})(?!\d)(?![\.\-]\d)", RegexOptions.IgnoreCase);
                    if (digitMatch.Success && int.TryParse(digitMatch.Groups[1].Value, out int num) && num <= 50)
                        return num;

                    return 0; // 0 means "all" or not specified
                }

                // Helper to convert word numbers to int
                int WordToNumber(string word)
                {
                    var map = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase)
                    {
                        {"one", 1}, {"two", 2}, {"three", 3}, {"four", 4}, {"five", 5},
                        {"six", 6}, {"seven", 7}, {"eight", 8}, {"nine", 9}, {"ten", 10},
                        {"eleven", 11}, {"twelve", 12}
                    };
                    return map.TryGetValue(word, out int val) ? val : 0;
                }

                // Helper to extract content filter keywords (what TYPE of details)
                // "add stair details" → "stair", "add the window and door details" → "window,door"
                string ExtractContentFilter(string input)
                {
                    var keywords = new List<string>();

                    // Common architectural detail keywords
                    var detailTypes = new[]
                    {
                        "stair", "stairs", "stairway",
                        "window", "windows", "glazing",
                        "door", "doors", "entry",
                        "wall", "walls", "partition",
                        "roof", "roofing", "eave", "fascia", "soffit",
                        "foundation", "footing", "slab",
                        "floor", "flooring",
                        "ceiling", "soffit",
                        "cabinet", "casework", "millwork",
                        "bathroom", "bath", "toilet", "restroom",
                        "kitchen",
                        "mechanical", "hvac", "duct",
                        "electrical", "panel",
                        "plumbing", "pipe", "drain",
                        "structural", "beam", "column", "connection",
                        "exterior", "interior",
                        "section", "elevation",
                        "jamb", "head", "sill", "threshold",
                        "flashing", "waterproofing",
                        "railing", "handrail", "guardrail",
                        "parapet", "coping"
                    };

                    foreach (var keyword in detailTypes)
                    {
                        if (Regex.IsMatch(input, $@"\b{keyword}\b", RegexOptions.IgnoreCase))
                        {
                            keywords.Add(keyword);
                        }
                    }

                    return string.Join(",", keywords);
                }

                // =============================================================================
                // COMPOUND COMMANDS - Handle "do X and do Y" patterns as batch operations
                // =============================================================================

                // Pattern: "create X sheets and add Y [view type] on each"
                // Supports: details, floor plans, 3D views, sections, elevations, etc.
                var compoundSheetViewsMatch = Regex.Match(lower,
                    @"(create|make|add)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+([a-z])\s*(sheet|sheets).*and.*(add|place|put)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*(detail|details|view|views|floor\s*plan|floor\s*plans|3d|section|sections|elevation|elevations|legend|legends)\s*(on|to)?\s*(each|every|all)",
                    RegexOptions.IgnoreCase);

                if (compoundSheetViewsMatch.Success)
                {
                    // Parse sheet creation part
                    int sheetCount = ExtractQuantity(compoundSheetViewsMatch.Groups[2].Value);
                    if (sheetCount == 0) sheetCount = ExtractQuantity(cleanedInput);
                    if (sheetCount == 0) sheetCount = 1;

                    string discipline = compoundSheetViewsMatch.Groups[3].Value.ToUpper();

                    // Parse view count
                    int viewCount = 0;
                    if (compoundSheetViewsMatch.Groups[6].Success && !string.IsNullOrEmpty(compoundSheetViewsMatch.Groups[6].Value))
                        viewCount = ExtractQuantity(compoundSheetViewsMatch.Groups[6].Value);
                    if (viewCount == 0) viewCount = 6; // Default

                    // SMART: Detect what type of view the user wants
                    string viewTypeWord = compoundSheetViewsMatch.Groups[7].Value.ToLower();
                    string viewType = "drafting"; // Default
                    string viewTypeDesc = "details";

                    if (viewTypeWord.Contains("floor") || viewTypeWord.Contains("plan"))
                    {
                        viewType = "floorplan";
                        viewTypeDesc = "floor plans";
                    }
                    else if (viewTypeWord.Contains("3d"))
                    {
                        viewType = "3d";
                        viewTypeDesc = "3D views";
                    }
                    else if (viewTypeWord.Contains("section"))
                    {
                        viewType = "section";
                        viewTypeDesc = "sections";
                    }
                    else if (viewTypeWord.Contains("elevation"))
                    {
                        viewType = "elevation";
                        viewTypeDesc = "elevations";
                    }
                    else if (viewTypeWord.Contains("legend"))
                    {
                        viewType = "legend";
                        viewTypeDesc = "legends";
                    }
                    else if (viewTypeWord.Contains("detail") || viewTypeWord.Contains("drafting"))
                    {
                        viewType = "drafting";
                        viewTypeDesc = "details";
                    }
                    else if (viewTypeWord.Contains("view"))
                    {
                        viewType = "all";
                        viewTypeDesc = "views";
                    }

                    // Use stored range if available
                    int rangeStart = _context.PreferredRangeStart ?? 1;

                    // Return batch command with view type
                    return new ProcessedCommand
                    {
                        Success = true,
                        Method = "batchCreateSheetsWithDetails",
                        Parameters = JObject.FromObject(new {
                            sheetCount = sheetCount,
                            discipline = discipline,
                            rangeStart = rangeStart,
                            detailsPerSheet = viewCount,
                            layout = "auto",
                            viewType = viewType  // SMART: Pass detected view type
                        }),
                        Description = $"Create {sheetCount} {discipline} sheets (starting at {rangeStart}) and add {viewCount} {viewTypeDesc} to each",
                        Confidence = 0.95,
                        RequiresConfirmation = false,
                        Intent = UserIntent.Create,
                        Entities = new ExtractedEntities {
                            ElementType = "batch",
                            Name = $"{sheetCount} sheets + {viewCount} {viewTypeDesc} each",
                            Confidence = 0.95
                        }
                    };
                }

                // --- PLACE VIEWS ON SHEETS ---
                // SMART VIEW TYPE DETECTION - detects what TYPE of view user wants
                // "add details" → drafting views only
                // "add floor plans" → floor plans only
                // "add 3D view" → 3D views only
                // "add sections" → sections only
                // "add elevations" → elevations only
                // "add views" (generic) → all placeable views
                if (Regex.IsMatch(lower, @"(place|add|put|drop|insert|move|throw).*(detail|drafting|view|unused|floor\s*plan|3d|section|elevation|legend|ceiling|rcp).*(on|to|onto|in)\s*(all\s*)?(the\s*)?(sheet|sheets)") ||
                    Regex.IsMatch(lower, @"(sheet).*(add|place|put|get|needs?).*(detail|drafting|view|floor\s*plan|3d|section|elevation)"))
                {
                    string sheetNum = ExtractSheetNumber(cleanedInput);
                    int count = ExtractQuantity(cleanedInput);
                    string contentFilter = ExtractContentFilter(cleanedInput);

                    // SMART: Detect what type of view the user wants
                    string viewType = "drafting"; // Default to detail/drafting views
                    string viewTypeDesc = "details";

                    if (Regex.IsMatch(lower, @"\b(floor\s*plan|floorplan|plan|plans)\b") && !Regex.IsMatch(lower, @"\bceiling\b"))
                    {
                        viewType = "floorplan";
                        viewTypeDesc = "floor plans";
                    }
                    else if (Regex.IsMatch(lower, @"\b(ceiling\s*plan|ceilingplan|rcp|reflected)\b"))
                    {
                        viewType = "ceiling";
                        viewTypeDesc = "ceiling plans";
                    }
                    else if (Regex.IsMatch(lower, @"\b(3d|3-d|three\s*d|threed|perspective)\b"))
                    {
                        viewType = "3d";
                        viewTypeDesc = "3D views";
                    }
                    else if (Regex.IsMatch(lower, @"\b(section|sections)\b"))
                    {
                        viewType = "section";
                        viewTypeDesc = "sections";
                    }
                    else if (Regex.IsMatch(lower, @"\b(elevation|elevations)\b"))
                    {
                        viewType = "elevation";
                        viewTypeDesc = "elevations";
                    }
                    else if (Regex.IsMatch(lower, @"\b(legend|legends)\b"))
                    {
                        viewType = "legend";
                        viewTypeDesc = "legends";
                    }
                    else if (Regex.IsMatch(lower, @"\b(callout|callouts)\b"))
                    {
                        viewType = "callout";
                        viewTypeDesc = "callouts";
                    }
                    else if (Regex.IsMatch(lower, @"\b(detail|details|drafting)\b"))
                    {
                        viewType = "drafting";
                        viewTypeDesc = "details";
                    }
                    else if (Regex.IsMatch(lower, @"\b(view|views)\b") && !Regex.IsMatch(lower, @"\b(detail|drafting)\b"))
                    {
                        // Generic "views" without specifying type - use all
                        viewType = "all";
                        viewTypeDesc = "views";
                    }

                    // Build description
                    string desc;
                    if (!string.IsNullOrEmpty(contentFilter))
                        desc = count > 0 ? $"Place {count} {contentFilter} {viewTypeDesc} on sheet {sheetNum}" : $"Place {contentFilter} {viewTypeDesc} on sheet {sheetNum}";
                    else
                        desc = count > 0 ? $"Place {count} {viewTypeDesc} on sheet {sheetNum}" : $"Place {viewTypeDesc} on sheet {sheetNum}";

                    return new ProcessedCommand
                    {
                        Success = true,
                        Method = "placeMultipleViewsOnSheet",
                        Parameters = JObject.FromObject(new {
                            sheetNumber = sheetNum,
                            layout = "auto",
                            count = count,
                            contentFilter = contentFilter,
                            viewType = viewType  // SMART: Pass detected view type
                        }),
                        Description = desc,
                        Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Modify,
                        Entities = new ExtractedEntities { ElementType = viewTypeDesc, Name = sheetNum, Confidence = 0.95 }
                    };
                }

                // --- STANDALONE NUMBER RESPONSE ---
                // Catches: "200", "300", "A-200" when user is answering "What sheet number?"
                // Also catches count responses: "5", "five", "three"
                var standaloneNumMatch = Regex.Match(cleanedInput.Trim(), @"^([A-Za-z][-\s]?)?(\d{1,4})$");
                if (standaloneNumMatch.Success)
                {
                    int.TryParse(standaloneNumMatch.Groups[2].Value, out int numVal);

                    // Small number (1-20) = probably a count, not a range
                    if (numVal >= 1 && numVal <= 20 && _context.HasValidPreferences)
                    {
                        // User is answering "how many sheets?" - create them now!
                        _context.PreferredCount = numVal;
                        int rangeStart = _context.PreferredRangeStart ?? 1;
                        string discipline = _context.PreferredDiscipline ?? "";

                        // Clear preferences after use
                        var result = new ProcessedCommand
                        {
                            Success = true,
                            Method = "createSheetsIntelligent",
                            Parameters = JObject.FromObject(new {
                                count = numVal,
                                discipline = discipline,
                                rangeStart = rangeStart
                            }),
                            Description = $"Create {numVal} {discipline} sheets starting at {rangeStart}",
                            Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Create,
                            Entities = new ExtractedEntities { ElementType = "sheet", Name = $"{discipline} x{numVal}", Confidence = 0.95 }
                        };
                        _context.ClearPreferences();
                        return result;
                    }
                    // Large number (100+) = probably a range start
                    else if (numVal >= 100)
                    {
                        _context.PreferredRangeStart = numVal;
                        _context.PreferencesSetAt = DateTime.Now;

                        // If there's a discipline letter too (like "A-200" or "A 200")
                        if (standaloneNumMatch.Groups[1].Success && !string.IsNullOrEmpty(standaloneNumMatch.Groups[1].Value))
                        {
                            string disc = standaloneNumMatch.Groups[1].Value.Trim().Replace("-", "").Replace(" ", "");
                            if (!string.IsNullOrEmpty(disc))
                                _context.PreferredDiscipline = disc.ToUpper();
                        }

                        // Acknowledge and wait for create command
                        string disc2 = !string.IsNullOrEmpty(_context.PreferredDiscipline) ? _context.PreferredDiscipline : "sheet";
                        return new ProcessedCommand
                        {
                            Success = true,
                            Method = "acknowledge",
                            Parameters = JObject.FromObject(new {
                                message = $"Got it - starting at {numVal}. How many {disc2} sheets?",
                                storedPreferences = new { rangeStart = numVal, discipline = _context.PreferredDiscipline }
                            }),
                            Description = $"Stored range start: {numVal}",
                            Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Unknown,
                            Entities = new ExtractedEntities { ElementType = "sheet", Confidence = 0.95 }
                        };
                    }
                }

                // --- WORD NUMBER RESPONSE ---
                // Catches: "five", "three", "ten" as count answers
                var wordNumMatch = Regex.Match(lower.Trim(), @"^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)$");
                if (wordNumMatch.Success && _context.HasValidPreferences)
                {
                    int count = WordToNumber(wordNumMatch.Groups[1].Value);
                    if (count > 0)
                    {
                        int rangeStart = _context.PreferredRangeStart ?? 1;
                        string discipline = _context.PreferredDiscipline ?? "";

                        var result = new ProcessedCommand
                        {
                            Success = true,
                            Method = "createSheetsIntelligent",
                            Parameters = JObject.FromObject(new {
                                count = count,
                                discipline = discipline,
                                rangeStart = rangeStart
                            }),
                            Description = $"Create {count} {discipline} sheets starting at {rangeStart}",
                            Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Create,
                            Entities = new ExtractedEntities { ElementType = "sheet", Name = $"{discipline} x{count}", Confidence = 0.95 }
                        };
                        _context.ClearPreferences();
                        return result;
                    }
                }

                // --- HYBRID CONTEXT: Store preferences from conversational hints ---
                // Catches: "Let the A sheets be in the 200s", "put them in the 300s", "use 400 series"
                // Stores preferences for use in the NEXT command (hybrid LLM + fast execution)
                bool isPreferenceOnlyMessage = false;
                if (Regex.IsMatch(lower, @"(let|put|use|have|want|make).*(sheet|it|them|number).*(in\s+the\s+\d|at\s+\d|\d+\s*series|be\s+\d)"))
                {
                    // Extract range preference
                    var inTheMatch = Regex.Match(lower, @"in\s+the\s+(\d)00s?");
                    if (inTheMatch.Success)
                    {
                        _context.PreferredRangeStart = int.Parse(inTheMatch.Groups[1].Value) * 100;
                        _context.PreferencesSetAt = DateTime.Now;
                    }

                    var startAtMatch = Regex.Match(lower, @"(start|at|be)\s*(\d{2,4})");
                    if (startAtMatch.Success)
                    {
                        int.TryParse(startAtMatch.Groups[2].Value, out int rangeVal);
                        if (rangeVal > 0)
                        {
                            _context.PreferredRangeStart = rangeVal;
                            _context.PreferencesSetAt = DateTime.Now;
                        }
                    }

                    var seriesMatch = Regex.Match(lower, @"(\d{2,4})\s*series");
                    if (seriesMatch.Success)
                    {
                        int.TryParse(seriesMatch.Groups[1].Value, out int rangeVal);
                        if (rangeVal > 0)
                        {
                            _context.PreferredRangeStart = rangeVal;
                            _context.PreferencesSetAt = DateTime.Now;
                        }
                    }

                    // Extract discipline if mentioned
                    var discMatch = Regex.Match(cleanedInput, @"\b([ASMEPCGLDTR])\s*(sheet|sheets)", RegexOptions.IgnoreCase);
                    if (discMatch.Success)
                    {
                        _context.PreferredDiscipline = discMatch.Groups[1].Value.ToUpper();
                        _context.PreferencesSetAt = DateTime.Now;
                    }

                    // Check if this is ONLY a preference message (no create command)
                    if (!Regex.IsMatch(lower, @"(create|add|make|new|insert)"))
                    {
                        isPreferenceOnlyMessage = true;
                        // Don't return yet - let it fall through or acknowledge
                    }
                }

                // --- CREATE/ADD NEW SHEETS (SMART + HYBRID) ---
                // Now uses stored context from previous messages!
                // Variations: "create 3 A sheets", "add A sheets", "create sheets A-601 to A-605", "new detail sheets"
                if (Regex.IsMatch(lower, @"(create|add|make|new|insert)\s*(a\s+)?(new\s+)?(\d+\s+)?(sheet|sheets|drawing|drawings)") ||
                    Regex.IsMatch(lower, @"(create|add|make|new)\s+[A-Za-z]\s*(sheet|sheets)") ||
                    isPreferenceOnlyMessage)  // Also trigger if we just got preferences and can act on them
                {
                    // Extract discipline letter (A, S, M, E, P, etc.)
                    string discipline = "";
                    var disciplineMatch = Regex.Match(cleanedInput, @"\b([ASMEPCGLDTR])\s*(sheet|sheets|-\d)", RegexOptions.IgnoreCase);
                    if (disciplineMatch.Success)
                        discipline = disciplineMatch.Groups[1].Value.ToUpper();

                    // Extract count (number words or digits)
                    int count = ExtractQuantity(cleanedInput);
                    if (count == 0) count = 1; // Default to 1 sheet

                    // Extract specific sheet number if provided
                    string sheetNum = ExtractSheetNumber(cleanedInput);

                    // Extract range if specified (e.g., "601 to 605", "601-605", "601 through 605")
                    int rangeStart = 0, rangeEnd = 0;
                    var rangeMatch = Regex.Match(cleanedInput, @"(\d{2,4})\s*(to|through|thru|-)\s*(\d{2,4})", RegexOptions.IgnoreCase);
                    if (rangeMatch.Success)
                    {
                        int.TryParse(rangeMatch.Groups[1].Value, out rangeStart);
                        int.TryParse(rangeMatch.Groups[3].Value, out rangeEnd);
                        count = rangeEnd - rangeStart + 1;
                    }

                    // SMART: Detect conversational number hints like "in the 200s", "start at 300", "200 series"
                    if (rangeStart == 0)
                    {
                        // "in the 200s", "in the 300s", etc.
                        var inTheMatch = Regex.Match(lower, @"in\s+the\s+(\d)00s?");
                        if (inTheMatch.Success)
                            rangeStart = int.Parse(inTheMatch.Groups[1].Value) * 100;

                        // "start at 200", "starting at 300", "begin at 400"
                        var startAtMatch = Regex.Match(lower, @"(start|starting|begin|beginning)\s*(at|with|from)?\s*(\d{2,4})");
                        if (startAtMatch.Success)
                            int.TryParse(startAtMatch.Groups[3].Value, out rangeStart);

                        // "200 series", "300 series", "use 400 series"
                        var seriesMatch = Regex.Match(lower, @"(\d{2,4})\s*series");
                        if (seriesMatch.Success)
                            int.TryParse(seriesMatch.Groups[1].Value, out rangeStart);

                        // "number them 200", "numbered 300", "number 400"
                        var numberMatch = Regex.Match(lower, @"number(ed|ing)?\s*(them|it)?\s*(\d{2,4})");
                        if (numberMatch.Success)
                            int.TryParse(numberMatch.Groups[3].Value, out rangeStart);

                        // "be in the 200s", "be 200"
                        var beMatch = Regex.Match(lower, @"be\s+(in\s+the\s+)?(\d)00s?");
                        if (beMatch.Success)
                            rangeStart = int.Parse(beMatch.Groups[2].Value) * 100;
                    }

                    // HYBRID: Use stored context from previous messages if still no rangeStart
                    if (rangeStart == 0 && _context.HasValidPreferences && _context.PreferredRangeStart.HasValue)
                    {
                        rangeStart = _context.PreferredRangeStart.Value;
                    }

                    // HYBRID: Use stored discipline if none found in current message
                    if (string.IsNullOrEmpty(discipline) && !string.IsNullOrEmpty(_context.PreferredDiscipline))
                    {
                        discipline = _context.PreferredDiscipline;
                    }

                    // Handle preference-only message: acknowledge and wait for action command
                    if (isPreferenceOnlyMessage && !Regex.IsMatch(lower, @"(create|add|make|new|insert)"))
                    {
                        // Store and acknowledge - user will give create command next
                        string ackMsg = $"Got it - {discipline} sheets in the {rangeStart}s. ";
                        if (_context.PreferredCount.HasValue)
                            ackMsg += $"Ready to create {_context.PreferredCount.Value} sheets.";
                        else
                            ackMsg += "How many sheets do you need?";

                        return new ProcessedCommand
                        {
                            Success = true,
                            Method = "acknowledge",  // No-op method, just acknowledgment
                            Parameters = JObject.FromObject(new {
                                message = ackMsg,
                                storedPreferences = new {
                                    rangeStart = rangeStart,
                                    discipline = discipline
                                }
                            }),
                            Description = ackMsg,
                            Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Unknown,
                            Entities = new ExtractedEntities { ElementType = "sheet", Confidence = 0.95 }
                        };
                    }

                    // Extract sheet name if quoted
                    string sheetName = ExtractQuotedName(cleanedInput);

                    // Detect common sheet types from keywords
                    string sheetType = "";
                    if (Regex.IsMatch(lower, @"\b(detail|details)\b")) { sheetType = "DETAILS"; discipline = string.IsNullOrEmpty(discipline) ? "A" : discipline; }
                    else if (Regex.IsMatch(lower, @"\b(floor\s*plan|plan)\b")) { sheetType = "FLOOR PLAN"; discipline = string.IsNullOrEmpty(discipline) ? "A" : discipline; }
                    else if (Regex.IsMatch(lower, @"\b(elevation|elevations)\b")) { sheetType = "ELEVATIONS"; discipline = string.IsNullOrEmpty(discipline) ? "A" : discipline; }
                    else if (Regex.IsMatch(lower, @"\b(section|sections)\b")) { sheetType = "SECTIONS"; discipline = string.IsNullOrEmpty(discipline) ? "A" : discipline; }
                    else if (Regex.IsMatch(lower, @"\b(structural)\b")) { sheetType = "STRUCTURAL"; discipline = "S"; }
                    else if (Regex.IsMatch(lower, @"\b(mechanical|hvac)\b")) { sheetType = "MECHANICAL"; discipline = "M"; }
                    else if (Regex.IsMatch(lower, @"\b(electrical)\b")) { sheetType = "ELECTRICAL"; discipline = "E"; }
                    else if (Regex.IsMatch(lower, @"\b(plumbing)\b")) { sheetType = "PLUMBING"; discipline = "P"; }

                    // If single sheet with specific number, use simple createSheet
                    if (count == 1 && !string.IsNullOrEmpty(sheetNum))
                    {
                        return new ProcessedCommand
                        {
                            Success = true,
                            Method = "createSheet",
                            Parameters = JObject.FromObject(new { sheetNumber = sheetNum, sheetName = sheetName ?? sheetType }),
                            Description = $"Create sheet {sheetNum}",
                            Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Create,
                            Entities = new ExtractedEntities { ElementType = "sheet", Name = sheetNum, Confidence = 0.95 }
                        };
                    }

                    // For batch creation, use createSheetsIntelligent (new method)
                    return new ProcessedCommand
                    {
                        Success = true,
                        Method = "createSheetsIntelligent",
                        Parameters = JObject.FromObject(new {
                            count = count,
                            discipline = discipline,
                            rangeStart = rangeStart > 0 ? rangeStart : (int?)null,
                            rangeEnd = rangeEnd > 0 ? rangeEnd : (int?)null,
                            sheetType = sheetType,
                            sheetName = sheetName
                        }),
                        Description = count > 1
                            ? $"Create {count} {discipline} sheets" + (rangeStart > 0 ? $" ({rangeStart}-{rangeEnd})" : " (auto-numbered)")
                            : $"Create {discipline} sheet (auto-numbered)",
                        Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Create,
                        Entities = new ExtractedEntities { ElementType = "sheet", Name = $"{discipline} x{count}", Confidence = 0.95 }
                    };
                }

                // --- LIST/SHOW SHEETS ---
                // Variations: "show sheets", "list all sheets", "what sheets", "get sheets"
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(sheet|sheets|drawings)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getSheets",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all sheets", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "sheet", Confidence = 0.95 }
                    };
                }

                // --- CREATE/ADD DETAIL VIEWS ---
                // Variations: "create detail", "new drafting view", "add detail view", "make a detail"
                // MUST NOT match "add details TO sheets" or "add details ON sheets" - those are placement commands
                if (Regex.IsMatch(lower, @"(create|add|make|new|insert)\s*(a\s+)?(new\s+)?(detail|drafting)\s*(view)?") &&
                    !Regex.IsMatch(lower, @"(detail|details)\s*(to|on|onto)\s*(all|the|sheet|sheets)"))
                {
                    string viewName = ExtractQuotedName(cleanedInput);
                    return new ProcessedCommand
                    {
                        Success = true, Method = "createDraftingView",
                        Parameters = JObject.FromObject(new { name = viewName }),
                        Description = string.IsNullOrEmpty(viewName) ? "Create drafting view" : $"Create drafting view '{viewName}'",
                        Confidence = 0.95, RequiresConfirmation = false, Intent = UserIntent.Create,
                        Entities = new ExtractedEntities { ElementType = "detail view", Name = viewName, Confidence = 0.95 }
                    };
                }

                // --- LIST/SHOW VIEWS ---
                // Variations: "show views", "list all views", "what views", "get views", "show details"
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(view|views|detail|details|drafting)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getViews",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all views", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "view", Confidence = 0.95 }
                    };
                }

                // --- GO TO / OPEN / SWITCH TO SHEET ---
                // Variations: "go to sheet A-101", "open sheet", "switch to A-101"
                if (Regex.IsMatch(lower, @"(go\s*to|open|switch\s*to|show|navigate\s*to)\s*(sheet)?\s*[A-Z]+-?\d+"))
                {
                    string sheetNum = ExtractSheetNumber(cleanedInput);
                    return new ProcessedCommand
                    {
                        Success = true, Method = "switchToSheet",
                        Parameters = JObject.FromObject(new { sheetNumber = sheetNum }),
                        Description = $"Switch to sheet {sheetNum}", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.Find, Entities = new ExtractedEntities { ElementType = "sheet", Name = sheetNum, Confidence = 0.95 }
                    };
                }

                // --- CREATE WALLS ---
                // Variations: "create wall", "add walls", "draw a wall", "make wall"
                if (Regex.IsMatch(lower, @"(create|add|make|draw|new|insert)\s*(a\s+)?(new\s+)?(wall|walls)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "createWall",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Create wall", Confidence = 0.90, RequiresConfirmation = false,
                        Intent = UserIntent.Create, Entities = new ExtractedEntities { ElementType = "wall", Confidence = 0.90 }
                    };
                }

                // --- LIST/SHOW WALLS ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(wall|walls)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getWalls",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all walls", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "wall", Confidence = 0.95 }
                    };
                }

                // --- CREATE/PLACE DOORS ---
                if (Regex.IsMatch(lower, @"(create|add|make|place|new|insert)\s*(a\s+)?(new\s+)?(door|doors|entry|entrance)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "placeDoor",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Place door", Confidence = 0.90, RequiresConfirmation = false,
                        Intent = UserIntent.Create, Entities = new ExtractedEntities { ElementType = "door", Confidence = 0.90 }
                    };
                }

                // --- LIST/SHOW DOORS ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(door|doors)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getDoors",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all doors", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "door", Confidence = 0.95 }
                    };
                }

                // --- CREATE/PLACE WINDOWS ---
                if (Regex.IsMatch(lower, @"(create|add|make|place|new|insert)\s*(a\s+)?(new\s+)?(window|windows)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "placeWindow",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Place window", Confidence = 0.90, RequiresConfirmation = false,
                        Intent = UserIntent.Create, Entities = new ExtractedEntities { ElementType = "window", Confidence = 0.90 }
                    };
                }

                // --- LIST/SHOW WINDOWS ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(window|windows)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getWindows",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all windows", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "window", Confidence = 0.95 }
                    };
                }

                // --- CREATE/TAG ROOMS ---
                if (Regex.IsMatch(lower, @"(create|add|make|new|insert)\s*(a\s+)?(new\s+)?(room|rooms|space)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "createRoom",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Create room", Confidence = 0.90, RequiresConfirmation = false,
                        Intent = UserIntent.Create, Entities = new ExtractedEntities { ElementType = "room", Confidence = 0.90 }
                    };
                }

                // --- LIST/SHOW ROOMS ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(room|rooms|space|spaces)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getRooms",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all rooms", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "room", Confidence = 0.95 }
                    };
                }

                // --- SHOW LEVELS ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(level|levels|floor|floors|story|stories)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getLevels",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all levels", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "level", Confidence = 0.95 }
                    };
                }

                // --- CREATE SCHEDULE ---
                if (Regex.IsMatch(lower, @"(create|add|make|new|insert)\s*(a\s+)?(new\s+)?(schedule|table)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "createSchedule",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Create schedule", Confidence = 0.90, RequiresConfirmation = false,
                        Intent = UserIntent.Create, Entities = new ExtractedEntities { ElementType = "schedule", Confidence = 0.90 }
                    };
                }

                // --- LIST SCHEDULES ---
                if (Regex.IsMatch(lower, @"(show|list|get|display|what|see|find)\s*(all\s+)?(the\s+)?(schedule|schedules|table|tables)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getSchedules",
                        Parameters = JObject.FromObject(new { }),
                        Description = "List all schedules", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.List, Entities = new ExtractedEntities { ElementType = "schedule", Confidence = 0.95 }
                    };
                }

                // --- UNDO ---
                if (Regex.IsMatch(lower, @"^(undo|go\s*back|reverse|revert)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "undo",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Undo last action", Confidence = 0.99, RequiresConfirmation = false,
                        Intent = UserIntent.Modify, Entities = new ExtractedEntities { Confidence = 0.99 }
                    };
                }

                // --- REDO ---
                if (Regex.IsMatch(lower, @"^(redo|go\s*forward)"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "redo",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Redo last action", Confidence = 0.99, RequiresConfirmation = false,
                        Intent = UserIntent.Modify, Entities = new ExtractedEntities { Confidence = 0.99 }
                    };
                }

                // --- SAVE ---
                if (Regex.IsMatch(lower, @"^(save|save\s*(the\s+)?(project|model|file))"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "save",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Save project", Confidence = 0.99, RequiresConfirmation = false,
                        Intent = UserIntent.Modify, Entities = new ExtractedEntities { Confidence = 0.99 }
                    };
                }

                // --- PROJECT INFO ---
                if (Regex.IsMatch(lower, @"(project\s*(info|information|details)|what\s*(project|model)|about\s*this\s*(project|model))"))
                {
                    return new ProcessedCommand
                    {
                        Success = true, Method = "getProjectInfo",
                        Parameters = JObject.FromObject(new { }),
                        Description = "Get project information", Confidence = 0.95, RequiresConfirmation = false,
                        Intent = UserIntent.Find, Entities = new ExtractedEntities { Confidence = 0.95 }
                    };
                }

                // =============================================================================
                // END OF NATURAL LANGUAGE SHORTCUTS
                // =============================================================================

                // Layer 2: Classify intent (no LLM needed)
                UserIntent intent = ClassifyIntent(cleanedInput);

                // Layer 3: Extract entities (no LLM needed)
                ExtractedEntities entities = ExtractEntities(cleanedInput);

                // Layer 4: Check if we need clarification
                string clarification = GetClarificationNeeded(intent, entities, cleanedInput);
                if (!string.IsNullOrEmpty(clarification))
                {
                    // Store context for follow-up
                    _context.LastIntent = intent;
                    _context.LastEntities = entities;
                    _context.PendingQuestion = clarification;
                    _context.LastInteraction = DateTime.Now;

                    return new ProcessedCommand
                    {
                        Success = false,
                        ClarificationNeeded = clarification,
                        Confidence = entities.Confidence,
                        Intent = intent,
                        Entities = entities
                    };
                }

                // Layer 5: Build command - use RULE-BASED for known high-confidence patterns
                // Skip LLM for patterns we can handle reliably without it
                ProcessedCommand command;

                bool useRuleBased = ShouldUseRuleBasedProcessing(intent, entities, cleanedInput);
                if (useRuleBased)
                {
                    // High-confidence pattern - skip the weak local LLM
                    command = BuildCommandRuleBased(intent, entities);
                    command.Confidence = 0.95; // Boost confidence for rule-based
                }
                else
                {
                    // Complex request - try LLM
                    command = await BuildCommandWithLLMAsync(intent, entities, cleanedInput);
                }

                // Layer 6: Validate command
                if (!ValidateCommand(command))
                {
                    return new ProcessedCommand
                    {
                        Success = false,
                        ClarificationNeeded = GetHelpfulSuggestions(intent, entities),
                        Confidence = 0.3,
                        Intent = intent,
                        Entities = entities
                    };
                }

                // Set intent and entities on command
                command.Intent = intent;
                command.Entities = entities;

                // Layer 7: Check if confirmation needed
                if (ShouldConfirm(intent, command))
                {
                    command.RequiresConfirmation = true;
                    command.ClarificationNeeded = GetConfirmationMessage(command);
                }

                // Layer 8: Apply safe defaults
                ApplySafeDefaults(command, entities);

                return command;
            }
            catch (Exception ex)
            {
                return new ProcessedCommand
                {
                    Success = false,
                    ClarificationNeeded = $"I encountered an issue: {ex.Message}. Could you try rephrasing?",
                    Confidence = 0,
                    Intent = UserIntent.Unknown,
                    Entities = new ExtractedEntities()
                };
            }
        }

        /// <summary>
        /// Process a follow-up answer to a previous clarification question.
        /// </summary>
        public async Task<ProcessedCommand> ProcessFollowUpAsync(string answer)
        {
            if (_context.PendingQuestion == null ||
                (DateTime.Now - _context.LastInteraction).TotalMinutes > 5)
            {
                // Context expired, treat as new input
                return await ProcessInputAsync(answer);
            }

            // Merge answer with previous context
            var entities = _context.LastEntities ?? new ExtractedEntities();

            // Update entities based on answer
            UpdateEntitiesFromAnswer(entities, answer);

            // Try to build command again
            string combinedInput = $"{_context.LastIntent}: {entities.ElementType} {entities.Name} {answer}";
            return await BuildCommandWithLLMAsync(_context.LastIntent, entities, combinedInput);
        }

        /// <summary>
        /// Determines if we should skip the LLM and use rule-based processing.
        /// Used for high-confidence patterns where the local LLM might fail.
        /// </summary>
        private bool ShouldUseRuleBasedProcessing(UserIntent intent, ExtractedEntities entities, string input)
        {
            string lower = input.ToLower();

            // Pattern 1: "add/place views/details to/on sheet" - ALWAYS use rule-based
            if (intent == UserIntent.Modify &&
                (entities.ElementType == "detail view" || entities.ElementType == "view" || entities.ElementType == "viewport") &&
                Regex.IsMatch(lower, @"\b(to|on|onto)\s+(sheet|the sheet)\b"))
            {
                return true;
            }

            // Pattern 2: Simple "create sheet X" - use rule-based
            if (intent == UserIntent.Create && entities.ElementType == "sheet" && !string.IsNullOrEmpty(entities.Name))
            {
                return true;
            }

            // Pattern 3: Simple "get/find/show sheets/doors/windows" - use rule-based
            if ((intent == UserIntent.Find || intent == UserIntent.List) &&
                !string.IsNullOrEmpty(entities.ElementType))
            {
                return true;
            }

            // Pattern 4: Any request with "sheet" in it that's NOT about creating - use rule-based
            // This catches "get sheet A-601", "find sheet", etc.
            if (lower.Contains("sheet") && intent != UserIntent.Create)
            {
                return true;
            }

            // Default: use LLM for complex/ambiguous requests
            return false;
        }

        #endregion

        #region Layer 1: Input Cleaning

        private string CleanInput(string input)
        {
            if (string.IsNullOrWhiteSpace(input))
                return string.Empty;

            // Normalize whitespace
            string cleaned = Regex.Replace(input.Trim(), @"\s+", " ");

            // Apply known corrections
            foreach (var correction in _corrections)
            {
                // Word boundary matching to avoid partial replacements
                string pattern = $@"\b{Regex.Escape(correction.Key)}\b";
                cleaned = Regex.Replace(cleaned, pattern, correction.Value, RegexOptions.IgnoreCase);
            }

            return cleaned;
        }

        #endregion

        #region Layer 2: Intent Classification

        private UserIntent ClassifyIntent(string input)
        {
            string lower = input.ToLower();

            // SPECIAL CASE: "add/place X to/on sheet" means placing views, not creating
            // This must be checked BEFORE the general intent patterns
            if (Regex.IsMatch(lower, @"\b(add|place|put)\b.*\b(to|on|onto)\s+(sheet|the sheet)\b"))
            {
                // This is a Modify intent - placing views on an existing sheet
                return UserIntent.Modify;
            }

            foreach (var intentPattern in _intentPatterns)
            {
                if (intentPattern.Value.Any(word =>
                    Regex.IsMatch(lower, $@"\b{Regex.Escape(word)}\b")))
                {
                    return (UserIntent)Enum.Parse(typeof(UserIntent), intentPattern.Key);
                }
            }

            // Check for implicit intents
            // If they mention an element type without a verb, likely want to create or find
            foreach (var element in _elementPatterns)
            {
                if (element.Value.Any(word => lower.Contains(word)))
                {
                    // If it's a question word structure, it's a question
                    if (Regex.IsMatch(lower, @"^(what|how|where|which|is|are|can|does)"))
                        return UserIntent.Question;

                    // Default to Create for bare element mentions
                    return UserIntent.Create;
                }
            }

            return UserIntent.Unknown;
        }

        #endregion

        #region Layer 3: Entity Extraction

        private ExtractedEntities ExtractEntities(string input)
        {
            var entities = new ExtractedEntities { Confidence = 0.5 };
            string lower = input.ToLower();

            // Extract element type - find LONGEST/MOST SPECIFIC match
            // This prevents "sheet" from matching before "detail view" in "place detail views on sheet"
            string bestMatch = null;
            int bestMatchLength = 0;

            foreach (var element in _elementPatterns)
            {
                foreach (var word in element.Value)
                {
                    if (Regex.IsMatch(lower, $@"\b{Regex.Escape(word)}\b"))
                    {
                        // Prefer longer matches (more specific)
                        if (word.Length > bestMatchLength)
                        {
                            bestMatch = element.Key;
                            bestMatchLength = word.Length;
                        }
                    }
                }
            }

            if (bestMatch != null)
            {
                entities.ElementType = bestMatch;
                entities.Confidence += 0.2;
            }

            // Extract sheet/view numbers (A-101, A1.1, etc.)
            var numberMatch = Regex.Match(input, @"[A-Z]-?\d+\.?\d*", RegexOptions.IgnoreCase);
            if (numberMatch.Success)
            {
                entities.Name = numberMatch.Value.ToUpper();
                entities.Confidence += 0.15;
            }

            // Extract quoted names
            var quotedMatch = Regex.Match(input, @"""([^""]+)""|'([^']+)'");
            if (quotedMatch.Success)
            {
                entities.Name = quotedMatch.Groups[1].Success ?
                    quotedMatch.Groups[1].Value : quotedMatch.Groups[2].Value;
                entities.Confidence += 0.15;
            }

            // Extract sizes (3x5, 10 feet, 8', etc.)
            var sizeMatch = Regex.Match(input, @"(\d+)\s*[x×]\s*(\d+)|\b(\d+)\s*(feet|foot|ft|'|inches|inch|in|"")");
            if (sizeMatch.Success)
            {
                entities.Size = sizeMatch.Value;
                entities.Confidence += 0.1;
            }

            // Extract location references
            var locationPatterns = new[]
            {
                @"\b(ground|first|second|third|fourth|fifth)\s*(floor|level)\b",
                @"\b(north|south|east|west|front|back|left|right)\s*(wall|side)?\b",
                @"\b(level|floor)\s*\d+\b",
                @"\bon\s+the\s+(\w+)\b"
            };

            foreach (var pattern in locationPatterns)
            {
                var locMatch = Regex.Match(lower, pattern);
                if (locMatch.Success)
                {
                    entities.Location = locMatch.Value;
                    entities.Confidence += 0.1;
                    break;
                }
            }

            // Cap confidence at 1.0
            entities.Confidence = Math.Min(entities.Confidence, 1.0);

            return entities;
        }

        #endregion

        #region Layer 4: Clarification

        private string GetClarificationNeeded(UserIntent intent, ExtractedEntities entities, string input)
        {
            // Unknown intent - offer help
            if (intent == UserIntent.Unknown)
            {
                return GetHelpMenu();
            }

            // Create intent but no element type
            if (intent == UserIntent.Create && string.IsNullOrEmpty(entities.ElementType))
            {
                return "What would you like to create?\n" +
                       "  - Sheet\n" +
                       "  - Wall\n" +
                       "  - Door or Window\n" +
                       "  - Room tag\n" +
                       "  - Text note\n" +
                       "  - Something else?";
            }

            // Create sheet but no number
            if (intent == UserIntent.Create &&
                entities.ElementType == "sheet" &&
                string.IsNullOrEmpty(entities.Name))
            {
                string nextSheet = GetNextAvailableSheetNumber();
                return $"What sheet number should I use?\n(Next available: {nextSheet})";
            }

            // Place something but no location
            if (intent == UserIntent.Create &&
                (entities.ElementType == "door" || entities.ElementType == "window") &&
                string.IsNullOrEmpty(entities.Location))
            {
                return $"Where should I place the {entities.ElementType}?\n" +
                       "(You can specify a wall or a location like 'north wall')";
            }

            // Low confidence - confirm understanding
            if (entities.Confidence < 0.4)
            {
                string understood = BuildUnderstandingStatement(intent, entities);
                return $"Just to confirm: {understood}\nIs that correct?";
            }

            return null; // No clarification needed
        }

        private string GetHelpMenu()
        {
            return "I can help you with:\n\n" +
                   "CREATE things:\n" +
                   "  - \"Create sheet A-101\"\n" +
                   "  - \"Add a door on the north wall\"\n" +
                   "  - \"Place a text note\"\n\n" +
                   "FIND things:\n" +
                   "  - \"Show me sheet A-101\"\n" +
                   "  - \"Find all doors\"\n" +
                   "  - \"Open the floor plan\"\n\n" +
                   "MODIFY things:\n" +
                   "  - \"Move the viewport\"\n" +
                   "  - \"Change the sheet name\"\n\n" +
                   "QUESTIONS:\n" +
                   "  - \"What's the minimum bathroom size?\"\n" +
                   "  - \"How many rooms are there?\"\n\n" +
                   "What would you like to do?";
        }

        private string GetHelpfulSuggestions(UserIntent intent, ExtractedEntities entities)
        {
            if (intent == UserIntent.Create)
            {
                return "I can help you create:\n" +
                       "  - Sheets: \"Create sheet A-101\"\n" +
                       "  - Walls: \"Create a wall from 0,0 to 10,0\"\n" +
                       "  - Doors: \"Add a door on wall 123\"\n" +
                       "  - Text: \"Add a text note saying 'Hello'\"\n\n" +
                       "Try being more specific about what you'd like to create.";
            }

            if (intent == UserIntent.Find)
            {
                return "I can help you find:\n" +
                       "  - Sheets: \"Show me all sheets\" or \"Open sheet A-101\"\n" +
                       "  - Elements: \"Find all doors\" or \"Show walls\"\n" +
                       "  - Views: \"Open the floor plan\"\n\n" +
                       "What are you looking for?";
            }

            return GetHelpMenu();
        }

        private string BuildUnderstandingStatement(UserIntent intent, ExtractedEntities entities)
        {
            string action = intent.ToString().ToLower();
            string element = entities.ElementType ?? "something";
            string name = !string.IsNullOrEmpty(entities.Name) ? $" called '{entities.Name}'" : "";
            string location = !string.IsNullOrEmpty(entities.Location) ? $" at {entities.Location}" : "";

            return $"You want to {action} a {element}{name}{location}";
        }

        #endregion

        #region Layer 5: LLM Command Building

        private async Task<ProcessedCommand> BuildCommandWithLLMAsync(
            UserIntent intent,
            ExtractedEntities entities,
            string originalInput)
        {
            // Build context-rich prompt
            string systemPrompt = BuildSystemPrompt(intent, entities);
            string userPrompt = $"USER REQUEST: {originalInput}\n\n" +
                               $"EXTRACTED INFO:\n" +
                               $"- Intent: {intent}\n" +
                               $"- Element: {entities.ElementType ?? "unknown"}\n" +
                               $"- Name: {entities.Name ?? "not specified"}\n" +
                               $"- Location: {entities.Location ?? "not specified"}\n\n" +
                               "Respond with a JSON object containing 'method' and 'parameters'. " +
                               "Only use methods from AVAILABLE_METHODS.";

            try
            {
                string response = await CallOllamaAsync(systemPrompt, userPrompt);

                // Parse LLM response
                var jsonMatch = Regex.Match(response, @"\{[\s\S]*\}");
                if (jsonMatch.Success)
                {
                    var parsed = JObject.Parse(jsonMatch.Value);

                    return new ProcessedCommand
                    {
                        Success = true,
                        Method = parsed["method"]?.ToString(),
                        Parameters = parsed["parameters"] as JObject ?? new JObject(),
                        Description = $"{intent} {entities.ElementType} {entities.Name}".Trim(),
                        Confidence = entities.Confidence
                    };
                }
            }
            catch (Exception ex)
            {
                // LLM failed, try rule-based fallback
                System.Diagnostics.Debug.WriteLine($"LLM call failed: {ex.Message}");
            }

            // Fallback to rule-based command building
            return BuildCommandRuleBased(intent, entities);
        }

        private string BuildSystemPrompt(UserIntent intent, ExtractedEntities entities)
        {
            string knowledgeContext = GetRelevantKnowledge(entities.ElementType);

            return $@"You are BIM Ops Studio, a Revit assistant.

RULES:
1. ONLY use methods from AVAILABLE_METHODS list below
2. If you cannot determine a required parameter, set it to null
3. Use the KNOWLEDGE section for domain-specific information
4. Respond with valid JSON only

KNOWLEDGE:
{knowledgeContext}

AVAILABLE_METHODS:
{GetMethodListForIntent(intent)}

Respond with JSON in this format:
{{
  ""method"": ""methodName"",
  ""parameters"": {{
    ""param1"": ""value1"",
    ""param2"": ""value2""
  }}
}}";
        }

        private string GetRelevantKnowledge(string elementType)
        {
            // Return relevant knowledge based on element type
            var knowledge = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                {"sheet", "- Sheet numbers follow pattern: DISC-#.# (e.g., A-1.0 for Architectural)\n" +
                          "- IMPORTANT: Do NOT pass titleblockId - system auto-detects from existing sheets\n" +
                          "- The most commonly used titleblock in the project will be used automatically\n" +
                          "- MULTIPLE VIEWS: Use placeMultipleViewsOnSheet for auto grid layout (avoids overlap!)\n" +
                          "- Layout presets: 'auto', 'grid-2x2', 'grid-3x2', 'row', 'column', etc."},

                {"view", "- DRAFTING VIEWS can only be on ONE sheet at a time\n" +
                         "- If 'View already placed on sheet' error: use duplicateView first, then place the duplicate\n" +
                         "- Or use removeViewport to remove from existing sheet, then place on new sheet\n" +
                         "- Detail views (callouts) reference model geometry and have same restriction\n" +
                         "- Floor plans, elevations, sections can also only be on one sheet at a time"},

                {"viewport", "- IMPORTANT: When placing MULTIPLE views, use placeMultipleViewsOnSheet for AUTO GRID LAYOUT\n" +
                             "- placeMultipleViewsOnSheet automatically arranges views to AVOID OVERLAPPING\n" +
                             "- Layouts: 'auto', 'row', 'column', 'grid-2x2', 'grid-3x2', 'grid-3x3', etc.\n" +
                             "- DRAFTING VIEWS can only be on ONE sheet at a time\n" +
                             "- If placeViewOnSheet fails with 'already placed': use duplicateView first\n" +
                             "- duplicateView creates a copy that can be placed on a different sheet\n" +
                             "- removeViewport removes a view from its current sheet"},

                {"multiple views", "- USE placeMultipleViewsOnSheet to place views with automatic grid layout\n" +
                             "- Pass viewIds as array: [123, 456, 789]\n" +
                             "- Layout presets: 'auto' (smart), 'row', 'column', 'grid-2x2', 'grid-3x2', 'grid-3x3'\n" +
                             "- 'left-column', 'right-column', 'top-row', 'bottom-row' for partial layouts\n" +
                             "- Views are AUTOMATICALLY positioned - no coordinates needed!"},

                {"drafting", "- IMPORTANT: Use placeMultipleViewsOnSheet for multiple drafting views!\n" +
                             "- Drafting views can only be placed on ONE sheet\n" +
                             "- To place same drafting view content on multiple sheets: duplicateView first\n" +
                             "- If already placed error: duplicateView(viewId) then placeViewOnSheet with new ID"},

                {"detail", "- Detail views (callouts) can only be on ONE sheet at a time\n" +
                           "- To show same detail on another sheet: duplicateView first, then place duplicate\n" +
                           "- Detail views reference model geometry unlike drafting views\n" +
                           "- WORKFLOW to add details to sheet:\n" +
                           "  1. getSheets() to find the sheet ID by number (e.g., A-601)\n" +
                           "  2. getViews() with filter for ViewType=DraftingView to find detail views\n" +
                           "  3. placeMultipleViewsOnSheet(sheetId, viewIds, layout='auto') for auto-placement"},

                {"text note", "- Use 3/32\" for notes (textContext: 'notes')\n" +
                              "- Use 3/16\" for labels (textContext: 'label')\n" +
                              "- Use 1/4\" for titles (textContext: 'title')"},

                {"door", "- Standard residential door: 3'-0\" x 6'-8\"\n" +
                         "- ADA accessible: min 32\" clear width\n" +
                         "- Verify wall ID before placement"},

                {"window", "- Standard window height: 4'-0\"\n" +
                           "- Sill height: 3'-0\" from floor\n" +
                           "- Verify wall ID before placement"},

                {"room", "- Florida bathroom minimum: 5' x 8'\n" +
                         "- Florida half bath minimum: 3' x 5'\n" +
                         "- Bedroom minimum: 70 sq ft\n" +
                         "- Ceiling height minimum: 7'-0\""},

                {"wall", "- Exterior wall: 6\" or 8\" typical\n" +
                         "- Interior wall: 4\" or 6\" typical\n" +
                         "- Fire-rated: 1-hour or 2-hour as required"}
            };

            string result = "";

            // Add injected knowledge first (highest priority)
            if (!string.IsNullOrEmpty(_injectedKnowledge))
            {
                result += "INJECTED CONTEXT:\n" + _injectedKnowledge + "\n\n";
            }

            // Add element-specific knowledge
            if (elementType != null && knowledge.ContainsKey(elementType))
            {
                result += "ELEMENT KNOWLEDGE:\n" + knowledge[elementType];
            }
            else
            {
                result += "- Follow project standards\n- Verify parameters before execution";
            }

            return result;
        }

        private string GetMethodListForIntent(UserIntent intent)
        {
            var methodsByIntent = new Dictionary<UserIntent, string[]>
            {
                {UserIntent.Create, new[] {
                    "createSheet(sheetNumber, sheetName?)",
                    "createWall(startX, startY, endX, endY, levelId?, wallTypeId?)",
                    "placeDoor(wallId, x, y, doorTypeId?)",
                    "placeWindow(wallId, x, y, windowTypeId?)",
                    "placeTextNote(text, x, y, viewId?, textContext?)",
                    "createRoom(levelId, x, y)",
                    "placeFamilyInstance(familyName, typeName, x, y, z?, levelId?)"
                }},
                {UserIntent.Find, new[] {
                    "getSheets()",
                    "getViews()",
                    "getElements(category?)",
                    "getDoors()",
                    "getWindows()",
                    "getRooms()",
                    "showElement(elementId)",
                    "zoomToElement(elementId)"
                }},
                {UserIntent.Modify, new[] {
                    "placeViewOnSheet(sheetId, viewId, x?, y?)",
                    "placeMultipleViewsOnSheet(sheetId, viewIds[], layout?)",
                    "setElementParameter(elementId, parameterName, value)",
                    "moveViewportOnSheet(viewportId, x, y)",
                    "renameSheet(sheetId, newNumber?, newName?)",
                    "updateTextNote(textNoteId, newText)",
                    "getViews() - to find drafting views to place",
                    "getSheets() - to find sheet ID by number"
                }},
                {UserIntent.Delete, new[] {
                    "deleteSheet(sheetId)",
                    "deleteElements(elementIds[])",
                    "deleteDoor(doorId)",
                    "deleteWindow(windowId)"
                }},
                {UserIntent.List, new[] {
                    "getSheets()",
                    "getViews()",
                    "getLevels()",
                    "getElements(category)",
                    "getCategories()"
                }},
                {UserIntent.Question, new[] {
                    "getProjectInfo()",
                    "getRoomArea(roomId)",
                    "getElementParameter(elementId, parameterName)",
                    "getScheduleData(scheduleId)"
                }}
            };

            if (methodsByIntent.ContainsKey(intent))
                return string.Join("\n", methodsByIntent[intent]);

            return string.Join("\n", _validMcpMethods.Take(20));
        }

        private ProcessedCommand BuildCommandRuleBased(UserIntent intent, ExtractedEntities entities)
        {
            // Simple rule-based command building as fallback
            var command = new ProcessedCommand
            {
                Success = true,
                Parameters = new JObject(),
                Confidence = entities.Confidence * 0.8 // Lower confidence for rule-based
            };

            switch (intent)
            {
                case UserIntent.Create:
                    if (entities.ElementType == "sheet")
                    {
                        command.Method = "createSheet";
                        if (!string.IsNullOrEmpty(entities.Name))
                            command.Parameters["sheetNumber"] = entities.Name;
                    }
                    else if (entities.ElementType == "text note")
                    {
                        command.Method = "placeTextNote";
                        command.Parameters["textContext"] = "notes";
                    }
                    break;

                case UserIntent.Find:
                    command.Method = entities.ElementType switch
                    {
                        "sheet" => "getSheets",
                        "door" => "getDoors",
                        "window" => "getWindows",
                        "room" => "getRooms",
                        "wall" => "getWalls",
                        _ => "getElements"
                    };
                    break;

                case UserIntent.List:
                    command.Method = "getElements";
                    if (!string.IsNullOrEmpty(entities.ElementType))
                        command.Parameters["category"] = entities.ElementType;
                    break;

                case UserIntent.Modify:
                    // Handle "place views on sheet" pattern
                    if (entities.ElementType == "detail view" || entities.ElementType == "view" ||
                        entities.ElementType == "viewport")
                    {
                        // This is a multi-step workflow - first get the sheet, then place views
                        command.Method = "placeMultipleViewsOnSheet";
                        command.Parameters["layout"] = "auto";
                        // Sheet number should be in entities.Name (e.g., A-601)
                        if (!string.IsNullOrEmpty(entities.Name))
                        {
                            command.Parameters["sheetNumber"] = entities.Name;
                        }
                        command.Description = $"Place views on sheet {entities.Name}";
                        command.RequiresConfirmation = false;
                        command.Confidence = 0.9; // High confidence for this pattern
                    }
                    else
                    {
                        // Generic modify - need more info
                        command.Success = false;
                        command.ClarificationNeeded = "What would you like to modify?";
                    }
                    break;

                default:
                    command.Success = false;
                    command.ClarificationNeeded = GetHelpMenu();
                    break;
            }

            command.Description = $"{intent} {entities.ElementType}".Trim();
            return command;
        }

        #endregion

        #region Layer 6: Command Validation

        private bool ValidateCommand(ProcessedCommand command)
        {
            if (string.IsNullOrEmpty(command.Method))
                return false;

            // Check if method exists
            if (!_validMcpMethods.Contains(command.Method))
            {
                // Try fuzzy matching
                var closest = _validMcpMethods
                    .OrderBy(m => LevenshteinDistance(m.ToLower(), command.Method.ToLower()))
                    .First();

                if (LevenshteinDistance(closest.ToLower(), command.Method.ToLower()) <= 3)
                {
                    command.Method = closest; // Auto-correct
                }
                else
                {
                    return false;
                }
            }

            return true;
        }

        private int LevenshteinDistance(string s1, string s2)
        {
            int[,] d = new int[s1.Length + 1, s2.Length + 1];

            for (int i = 0; i <= s1.Length; i++) d[i, 0] = i;
            for (int j = 0; j <= s2.Length; j++) d[0, j] = j;

            for (int i = 1; i <= s1.Length; i++)
            {
                for (int j = 1; j <= s2.Length; j++)
                {
                    int cost = s1[i - 1] == s2[j - 1] ? 0 : 1;
                    d[i, j] = Math.Min(Math.Min(
                        d[i - 1, j] + 1,
                        d[i, j - 1] + 1),
                        d[i - 1, j - 1] + cost);
                }
            }

            return d[s1.Length, s2.Length];
        }

        #endregion

        #region Layer 7: Confirmation

        private bool ShouldConfirm(UserIntent intent, ProcessedCommand command)
        {
            // Always confirm deletions
            if (intent == UserIntent.Delete)
                return true;

            // Confirm batch operations
            if (command.Method.Contains("All") ||
                command.Method.Contains("Batch") ||
                command.AffectedCount > 5)
                return true;

            // Confirm low confidence
            if (command.Confidence < 0.5)
                return true;

            return false;
        }

        private string GetConfirmationMessage(ProcessedCommand command)
        {
            if (command.Method.StartsWith("delete", StringComparison.OrdinalIgnoreCase))
            {
                return $"Are you sure you want to delete? This cannot be undone.\n" +
                       $"Action: {command.Description}\n" +
                       "Reply 'yes' to confirm or 'no' to cancel.";
            }

            if (command.AffectedCount > 1)
            {
                return $"This will affect {command.AffectedCount} elements.\n" +
                       $"Action: {command.Description}\n" +
                       "Reply 'yes' to proceed or 'no' to cancel.";
            }

            return $"Please confirm: {command.Description}\n" +
                   "Reply 'yes' to proceed or 'no' to cancel.";
        }

        #endregion

        #region Layer 8: Safe Defaults

        private void ApplySafeDefaults(ProcessedCommand command, ExtractedEntities entities)
        {
            if (command.Parameters == null)
                command.Parameters = new JObject();

            // Apply defaults based on method
            switch (command.Method)
            {
                case "placeTextNote":
                    if (command.Parameters["textContext"] == null)
                        command.Parameters["textContext"] = "notes"; // 3/32"
                    break;

                case "createSheet":
                    if (command.Parameters["sheetNumber"] == null && !string.IsNullOrEmpty(entities.Name))
                        command.Parameters["sheetNumber"] = entities.Name;
                    break;

                case "createWall":
                    // Default to interior wall type if not specified
                    if (command.Parameters["wallTypeId"] == null)
                    {
                        // Will use first available interior wall type
                    }
                    break;
            }
        }

        #endregion

        #region Helper Methods

        private async Task<string> CallOllamaAsync(string systemPrompt, string userPrompt)
        {
            var request = new
            {
                model = _localModel,
                prompt = $"{systemPrompt}\n\n{userPrompt}",
                stream = false,
                options = new
                {
                    temperature = 0.1,  // Low temperature for more deterministic outputs
                    num_predict = 500,
                    num_gpu = 0,        // Force CPU mode - user's GPU doesn't have enough VRAM
                    num_thread = 16     // Use multiple CPU threads for better performance
                }
            };

            var content = new StringContent(
                JsonConvert.SerializeObject(request),
                System.Text.Encoding.UTF8,
                "application/json");

            var response = await _httpClient.PostAsync(_ollamaEndpoint, content);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
            var responseJson = JObject.Parse(responseBody);

            return responseJson["response"]?.ToString() ?? "";
        }

        private string GetNextAvailableSheetNumber()
        {
            try
            {
                var doc = _uiApp?.ActiveUIDocument?.Document;
                if (doc == null) return "A-1.0";

                var sheets = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSheet))
                    .Cast<ViewSheet>()
                    .Select(s => s.SheetNumber)
                    .ToList();

                // Find the next available A-#.# number
                for (int major = 1; major <= 99; major++)
                {
                    for (int minor = 0; minor <= 9; minor++)
                    {
                        string candidate = $"A-{major}.{minor}";
                        if (!sheets.Contains(candidate))
                            return candidate;
                    }
                }

                return "A-1.0";
            }
            catch
            {
                return "A-1.0";
            }
        }

        private void UpdateEntitiesFromAnswer(ExtractedEntities entities, string answer)
        {
            // Extract any new information from the answer
            var newEntities = ExtractEntities(answer);

            if (!string.IsNullOrEmpty(newEntities.Name))
                entities.Name = newEntities.Name;
            if (!string.IsNullOrEmpty(newEntities.Location))
                entities.Location = newEntities.Location;
            if (!string.IsNullOrEmpty(newEntities.Size))
                entities.Size = newEntities.Size;
            if (!string.IsNullOrEmpty(newEntities.ElementType) && string.IsNullOrEmpty(entities.ElementType))
                entities.ElementType = newEntities.ElementType;
        }

        /// <summary>
        /// Learn a new correction from user feedback.
        /// </summary>
        public void LearnCorrection(string original, string corrected)
        {
            string key = original.ToLower().Trim();
            string value = corrected.ToLower().Trim();

            if (!string.IsNullOrEmpty(key) && !string.IsNullOrEmpty(value) && key != value)
            {
                _corrections[key] = value;
                // Could persist to file here for cross-session learning
            }
        }

        #endregion
    }
}

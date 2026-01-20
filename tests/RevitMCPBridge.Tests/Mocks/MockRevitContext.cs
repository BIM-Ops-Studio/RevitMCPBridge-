using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace RevitMCPBridge.Tests.Mocks
{
    /// <summary>
    /// Mock Revit context for unit testing without actual Revit instance.
    /// Simulates Revit API responses for common operations.
    /// </summary>
    public class MockRevitContext
    {
        public Dictionary<int, MockElement> Elements { get; } = new Dictionary<int, MockElement>();
        public Dictionary<int, MockLevel> Levels { get; } = new Dictionary<int, MockLevel>();
        public Dictionary<int, MockView> Views { get; } = new Dictionary<int, MockView>();
        public Dictionary<int, MockSheet> Sheets { get; } = new Dictionary<int, MockSheet>();
        public Dictionary<int, MockRoom> Rooms { get; } = new Dictionary<int, MockRoom>();
        public Dictionary<int, MockWall> Walls { get; } = new Dictionary<int, MockWall>();
        public Dictionary<int, MockElementType> ElementTypes { get; } = new Dictionary<int, MockElementType>();

        private int _nextElementId = 100000;

        public MockRevitContext()
        {
            // Initialize with default data
            InitializeDefaults();
        }

        private void InitializeDefaults()
        {
            // Add default levels
            AddLevel(1, "Level 1", 0.0);
            AddLevel(2, "Level 2", 10.0);
            AddLevel(3, "Level 3", 20.0);

            // Add default wall types
            AddElementType(1001, "Basic Wall", "Walls");
            AddElementType(1002, "Generic - 8\"", "Walls");
            AddElementType(1003, "Exterior - Brick", "Walls");

            // Add default door types
            AddElementType(2001, "Single-Flush", "Doors");
            AddElementType(2002, "Double-Flush", "Doors");

            // Add default window types
            AddElementType(3001, "Fixed", "Windows");
            AddElementType(3002, "Casement", "Windows");

            // Add default views
            AddView(5001, "Level 1 - Floor Plan", "FloorPlan", 1);
            AddView(5002, "Level 2 - Floor Plan", "FloorPlan", 2);
            AddView(5003, "Section 1", "Section", null);
        }

        public int GetNextElementId()
        {
            return _nextElementId++;
        }

        public void AddLevel(int id, string name, double elevation)
        {
            Levels[id] = new MockLevel { Id = id, Name = name, Elevation = elevation };
        }

        public void AddElementType(int id, string name, string category)
        {
            ElementTypes[id] = new MockElementType { Id = id, Name = name, Category = category };
        }

        public void AddView(int id, string name, string viewType, int? levelId)
        {
            Views[id] = new MockView { Id = id, Name = name, ViewType = viewType, LevelId = levelId };
        }

        public MockWall CreateWall(double startX, double startY, double endX, double endY, int levelId, int wallTypeId, double height)
        {
            var id = GetNextElementId();
            var wall = new MockWall
            {
                Id = id,
                StartX = startX,
                StartY = startY,
                EndX = endX,
                EndY = endY,
                LevelId = levelId,
                WallTypeId = wallTypeId,
                Height = height,
                Length = Math.Sqrt(Math.Pow(endX - startX, 2) + Math.Pow(endY - startY, 2))
            };
            Walls[id] = wall;
            Elements[id] = wall;
            return wall;
        }

        public MockRoom CreateRoom(int levelId, double x, double y, string name = null)
        {
            var id = GetNextElementId();
            var room = new MockRoom
            {
                Id = id,
                LevelId = levelId,
                X = x,
                Y = y,
                Name = name ?? $"Room {id}",
                Area = 0 // Would be calculated from boundaries
            };
            Rooms[id] = room;
            Elements[id] = room;
            return room;
        }

        public MockSheet CreateSheet(string number, string name, int? titleBlockId)
        {
            var id = GetNextElementId();
            var sheet = new MockSheet
            {
                Id = id,
                Number = number,
                Name = name,
                TitleBlockId = titleBlockId
            };
            Sheets[id] = sheet;
            Elements[id] = sheet;
            return sheet;
        }

        public bool DeleteElement(int elementId)
        {
            if (Elements.ContainsKey(elementId))
            {
                Elements.Remove(elementId);
                Walls.Remove(elementId);
                Rooms.Remove(elementId);
                Sheets.Remove(elementId);
                Views.Remove(elementId);
                return true;
            }
            return false;
        }

        public MockElement GetElement(int elementId)
        {
            return Elements.ContainsKey(elementId) ? Elements[elementId] : null;
        }

        /// <summary>
        /// Simulate executing an MCP method and return mock response
        /// </summary>
        public string ExecuteMethod(string method, JObject parameters)
        {
            try
            {
                switch (method.ToLower())
                {
                    case "getlevels":
                    case "getalllevels":
                        return GetLevelsResponse();

                    case "getviews":
                    case "getallviews":
                        return GetViewsResponse();

                    case "getwalls":
                        return GetWallsResponse(parameters);

                    case "createwall":
                        return CreateWallResponse(parameters);

                    case "deletewall":
                    case "deleteelement":
                        return DeleteElementResponse(parameters);

                    case "getrooms":
                        return GetRoomsResponse(parameters);

                    case "createroom":
                        return CreateRoomResponse(parameters);

                    case "getprojectinfo":
                        return GetProjectInfoResponse();

                    case "getwalltypes":
                        return GetWallTypesResponse();

                    case "verifyelement":
                        return VerifyElementResponse(parameters);

                    default:
                        return JObject.FromObject(new
                        {
                            success = false,
                            error = $"Method '{method}' not implemented in mock"
                        }).ToString();
                }
            }
            catch (Exception ex)
            {
                return JObject.FromObject(new
                {
                    success = false,
                    error = ex.Message
                }).ToString();
            }
        }

        private string GetLevelsResponse()
        {
            var levelList = new List<object>();
            foreach (var level in Levels.Values)
            {
                levelList.Add(new
                {
                    levelId = level.Id,
                    name = level.Name,
                    elevation = level.Elevation
                });
            }

            return JObject.FromObject(new
            {
                success = true,
                levels = levelList
            }).ToString();
        }

        private string GetViewsResponse()
        {
            var viewList = new List<object>();
            foreach (var view in Views.Values)
            {
                viewList.Add(new
                {
                    viewId = view.Id,
                    name = view.Name,
                    viewType = view.ViewType
                });
            }

            return JObject.FromObject(new
            {
                success = true,
                views = viewList
            }).ToString();
        }

        private string GetWallsResponse(JObject parameters)
        {
            var wallList = new List<object>();
            foreach (var wall in Walls.Values)
            {
                wallList.Add(new
                {
                    wallId = wall.Id,
                    startX = wall.StartX,
                    startY = wall.StartY,
                    endX = wall.EndX,
                    endY = wall.EndY,
                    height = wall.Height,
                    length = wall.Length
                });
            }

            return JObject.FromObject(new
            {
                success = true,
                walls = wallList,
                count = wallList.Count
            }).ToString();
        }

        private string CreateWallResponse(JObject parameters)
        {
            var startX = parameters["startX"]?.Value<double>() ?? 0;
            var startY = parameters["startY"]?.Value<double>() ?? 0;
            var endX = parameters["endX"]?.Value<double>() ?? 0;
            var endY = parameters["endY"]?.Value<double>() ?? 0;
            var levelId = parameters["levelId"]?.Value<int>() ?? 1;
            var wallTypeId = parameters["wallTypeId"]?.Value<int>() ?? 1001;
            var height = parameters["height"]?.Value<double>() ?? 10.0;

            // Validation
            if (startX == endX && startY == endY)
            {
                return JObject.FromObject(new
                {
                    success = false,
                    error = "Wall must have non-zero length"
                }).ToString();
            }

            if (!Levels.ContainsKey(levelId))
            {
                return JObject.FromObject(new
                {
                    success = false,
                    error = $"Level {levelId} not found"
                }).ToString();
            }

            var wall = CreateWall(startX, startY, endX, endY, levelId, wallTypeId, height);

            return JObject.FromObject(new
            {
                success = true,
                wallId = wall.Id,
                length = wall.Length
            }).ToString();
        }

        private string DeleteElementResponse(JObject parameters)
        {
            var elementId = parameters["elementId"]?.Value<int>() ?? parameters["wallId"]?.Value<int>() ?? 0;

            if (elementId == 0)
            {
                return JObject.FromObject(new
                {
                    success = false,
                    error = "elementId is required"
                }).ToString();
            }

            var deleted = DeleteElement(elementId);

            return JObject.FromObject(new
            {
                success = deleted,
                error = deleted ? null : $"Element {elementId} not found"
            }).ToString();
        }

        private string GetRoomsResponse(JObject parameters)
        {
            var roomList = new List<object>();
            foreach (var room in Rooms.Values)
            {
                roomList.Add(new
                {
                    roomId = room.Id,
                    name = room.Name,
                    area = room.Area,
                    levelId = room.LevelId
                });
            }

            return JObject.FromObject(new
            {
                success = true,
                rooms = roomList,
                count = roomList.Count
            }).ToString();
        }

        private string CreateRoomResponse(JObject parameters)
        {
            var levelId = parameters["levelId"]?.Value<int>() ?? 1;
            var x = parameters["x"]?.Value<double>() ?? 0;
            var y = parameters["y"]?.Value<double>() ?? 0;

            if (!Levels.ContainsKey(levelId))
            {
                return JObject.FromObject(new
                {
                    success = false,
                    error = $"Level {levelId} not found"
                }).ToString();
            }

            var room = CreateRoom(levelId, x, y);

            return JObject.FromObject(new
            {
                success = true,
                roomId = room.Id,
                name = room.Name
            }).ToString();
        }

        private string GetProjectInfoResponse()
        {
            return JObject.FromObject(new
            {
                success = true,
                projectName = "Test Project",
                projectNumber = "2024-001",
                clientName = "Test Client",
                projectAddress = "123 Test Street"
            }).ToString();
        }

        private string GetWallTypesResponse()
        {
            var types = new List<object>();
            foreach (var type in ElementTypes.Values)
            {
                if (type.Category == "Walls")
                {
                    types.Add(new
                    {
                        typeId = type.Id,
                        name = type.Name
                    });
                }
            }

            return JObject.FromObject(new
            {
                success = true,
                wallTypes = types
            }).ToString();
        }

        private string VerifyElementResponse(JObject parameters)
        {
            var elementId = parameters["elementId"]?.Value<int>() ?? 0;
            var exists = Elements.ContainsKey(elementId);

            return JObject.FromObject(new
            {
                success = true,
                exists = exists,
                elementId = elementId
            }).ToString();
        }
    }

    #region Mock Element Classes

    public class MockElement
    {
        public int Id { get; set; }
        public string Category { get; set; }
    }

    public class MockLevel : MockElement
    {
        public string Name { get; set; }
        public double Elevation { get; set; }
    }

    public class MockView : MockElement
    {
        public string Name { get; set; }
        public string ViewType { get; set; }
        public int? LevelId { get; set; }
    }

    public class MockSheet : MockElement
    {
        public string Number { get; set; }
        public string Name { get; set; }
        public int? TitleBlockId { get; set; }
        public List<int> ViewportIds { get; set; } = new List<int>();
    }

    public class MockRoom : MockElement
    {
        public string Name { get; set; }
        public double Area { get; set; }
        public int LevelId { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
    }

    public class MockWall : MockElement
    {
        public double StartX { get; set; }
        public double StartY { get; set; }
        public double EndX { get; set; }
        public double EndY { get; set; }
        public double Height { get; set; }
        public double Length { get; set; }
        public int LevelId { get; set; }
        public int WallTypeId { get; set; }
    }

    public class MockElementType : MockElement
    {
        public string Name { get; set; }
    }

    #endregion
}

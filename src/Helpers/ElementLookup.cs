using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using RevitMCPBridge.Exceptions;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Helper utilities for looking up Revit elements.
    /// Provides consistent error handling and null-safety.
    /// </summary>
    public static class ElementLookup
    {
        #region Get By ID

        /// <summary>
        /// Get an element by ID with type casting and validation.
        /// </summary>
        public static T GetElement<T>(Document doc, int elementId, string elementType = null) where T : Element
        {
            var id = new ElementId(elementId);
            var element = doc.GetElement(id) as T;

            if (element == null)
            {
                throw MCPRevitException.ElementNotFound(elementId);
            }

            return element;
        }

        /// <summary>
        /// Get an element by ID, returning null if not found.
        /// </summary>
        public static T TryGetElement<T>(Document doc, int elementId) where T : Element
        {
            var id = new ElementId(elementId);
            return doc.GetElement(id) as T;
        }

        /// <summary>
        /// Get a level by ID.
        /// </summary>
        public static Level GetLevel(Document doc, int levelId)
        {
            var level = TryGetElement<Level>(doc, levelId);
            if (level == null)
            {
                throw MCPRevitException.LevelNotFound(levelId);
            }
            return level;
        }

        /// <summary>
        /// Get a wall by ID.
        /// </summary>
        public static Wall GetWall(Document doc, int wallId)
        {
            return GetElement<Wall>(doc, wallId, "Wall");
        }

        /// <summary>
        /// Get a room by ID.
        /// </summary>
        public static Room GetRoom(Document doc, int roomId)
        {
            return GetElement<Room>(doc, roomId, "Room");
        }

        /// <summary>
        /// Get a view by ID.
        /// </summary>
        public static View GetView(Document doc, int viewId)
        {
            return GetElement<View>(doc, viewId, "View");
        }

        /// <summary>
        /// Get a sheet by ID.
        /// </summary>
        public static ViewSheet GetSheet(Document doc, int sheetId)
        {
            return GetElement<ViewSheet>(doc, sheetId, "Sheet");
        }

        #endregion

        #region Find By Name/Type

        /// <summary>
        /// Get a wall type by name.
        /// </summary>
        public static WallType GetWallType(Document doc, string typeName)
        {
            var wallType = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(wt => wt.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase));

            if (wallType == null)
            {
                throw MCPRevitException.TypeNotFound(typeName, "Wall");
            }

            return wallType;
        }

        /// <summary>
        /// Get a wall type by ID.
        /// </summary>
        public static WallType GetWallType(Document doc, int typeId)
        {
            return GetElement<WallType>(doc, typeId, "WallType");
        }

        /// <summary>
        /// Get the default or first available wall type.
        /// </summary>
        public static WallType GetDefaultWallType(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(wt => wt.Kind == WallKind.Basic)
                ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(WallType))
                    .Cast<WallType>()
                    .FirstOrDefault();
        }

        /// <summary>
        /// Get a family symbol by name.
        /// </summary>
        public static FamilySymbol GetFamilySymbol(Document doc, string familyName, string typeName)
        {
            var symbol = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .FirstOrDefault(fs =>
                    fs.Family.Name.Equals(familyName, StringComparison.OrdinalIgnoreCase) &&
                    fs.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase));

            if (symbol == null)
            {
                throw MCPRevitException.TypeNotFound($"{familyName}: {typeName}", "Family");
            }

            return symbol;
        }

        /// <summary>
        /// Get a family symbol by ID.
        /// </summary>
        public static FamilySymbol GetFamilySymbol(Document doc, int symbolId)
        {
            var symbol = GetElement<FamilySymbol>(doc, symbolId, "FamilySymbol");

            // Ensure symbol is activated
            if (!symbol.IsActive)
            {
                symbol.Activate();
                doc.Regenerate();
            }

            return symbol;
        }

        /// <summary>
        /// Get the default level (first level or "Level 1").
        /// </summary>
        public static Level GetDefaultLevel(Document doc)
        {
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            // Try to find "Level 1" first
            var level1 = levels.FirstOrDefault(l =>
                l.Name.Equals("Level 1", StringComparison.OrdinalIgnoreCase) ||
                l.Name.Equals("Level 01", StringComparison.OrdinalIgnoreCase));

            return level1 ?? levels.FirstOrDefault();
        }

        #endregion

        #region Collect Elements

        /// <summary>
        /// Get all elements of a category.
        /// </summary>
        public static IEnumerable<T> GetElements<T>(Document doc, BuiltInCategory category) where T : Element
        {
            return new FilteredElementCollector(doc)
                .OfCategory(category)
                .WhereElementIsNotElementType()
                .Cast<T>();
        }

        /// <summary>
        /// Get all elements of a class.
        /// </summary>
        public static IEnumerable<T> GetElements<T>(Document doc) where T : Element
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(T))
                .Cast<T>();
        }

        /// <summary>
        /// Get all levels in order of elevation.
        /// </summary>
        public static IEnumerable<Level> GetAllLevels(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation);
        }

        /// <summary>
        /// Get all views (excluding templates).
        /// </summary>
        public static IEnumerable<View> GetAllViews(Document doc, bool excludeTemplates = true)
        {
            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>();

            if (excludeTemplates)
            {
                views = views.Where(v => !v.IsTemplate);
            }

            return views;
        }

        /// <summary>
        /// Get all sheets.
        /// </summary>
        public static IEnumerable<ViewSheet> GetAllSheets(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(ViewSheet))
                .Cast<ViewSheet>();
        }

        /// <summary>
        /// Get all rooms.
        /// </summary>
        public static IEnumerable<Room> GetAllRooms(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
                .Cast<Room>();
        }

        /// <summary>
        /// Get all walls.
        /// </summary>
        public static IEnumerable<Wall> GetAllWalls(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>();
        }

        #endregion

        #region Type Collections

        /// <summary>
        /// Get all wall types.
        /// </summary>
        public static IEnumerable<WallType> GetAllWallTypes(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>();
        }

        /// <summary>
        /// Get all family symbols of a category.
        /// </summary>
        public static IEnumerable<FamilySymbol> GetFamilySymbols(Document doc, BuiltInCategory category)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .OfCategory(category)
                .Cast<FamilySymbol>();
        }

        #endregion
    }
}

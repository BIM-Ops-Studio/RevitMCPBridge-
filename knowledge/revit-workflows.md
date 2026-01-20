# Revit Workflows - Step-by-Step Instructions

When user asks for these tasks, follow these EXACT steps:

---

## WORKFLOW: "Review the drawing" or "Check this view"
1. Call `getActiveView` to get current view info
2. Call `captureActiveView` to take a screenshot
3. Call `getElements` with the view's category to count elements
4. Analyze the screenshot for:
   - Missing room tags (rooms without labels)
   - Overlapping annotations (text on top of text)
   - Missing dimensions (walls without measurements)
   - Untagged doors/windows
5. Report findings with SPECIFIC element counts and locations

---

## WORKFLOW: "Tag all rooms" or "Add room tags"
1. Call `getRooms` to get all rooms
2. For each room, check if it has a tag using `getElements` category="RoomTags"
3. For untagged rooms, call `suggestPlacementLocation` to find best tag position
4. Call `tagElements` to place the tag
5. Report: "Tagged X rooms, Y were already tagged"

---

## WORKFLOW: "Check for overlaps" or "Find conflicts"
1. Call `getActiveView` to get view bounds
2. Call `checkForOverlaps` to find annotation conflicts
3. For each conflict, report:
   - Element 1 ID and type
   - Element 2 ID and type
   - Overlap location
4. Suggest fixes: "Move element X to position Y"

---

## WORKFLOW: "Place annotation" or "Add text/keynote"
NEVER place blindly. Always:
1. Call `suggestPlacementLocation` with desired area
2. Check the suggested location for conflicts
3. Place at the suggested location
4. Verify placement with `captureActiveView`

---

## WORKFLOW: "List all sheets" or "Show sheets"
1. Call `getSheets` to get all sheets
2. Organize by discipline (A=Arch, S=Struct, M=Mech, etc.)
3. Report count per discipline
4. Flag any sheets missing views

---

## WORKFLOW: "QC Check" or "Quality control"
Run ALL these checks:
1. `getRooms` - Count rooms, check for untagged
2. `getDoors` - Count doors, check for untagged
3. `getWindows` - Count windows, check for untagged
4. `getSheets` - Check all sheets have views
5. `checkForOverlaps` - Find annotation conflicts
Report a summary with counts and issues found.

---

## WORKFLOW: "What's in this project?" or "Project summary"
1. Call `getProjectInfo` for project name, number, address
2. Call `getLevels` to list all levels
3. Call `getViews` to count views by type
4. Call `getSheets` to count sheets
5. Call `getRooms` to count rooms
6. Report organized summary with counts

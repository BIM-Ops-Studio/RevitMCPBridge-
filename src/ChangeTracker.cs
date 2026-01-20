using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;
using Newtonsoft.Json;

namespace RevitMCPBridge
{
    /// <summary>
    /// Tracks real-time changes in Revit documents including element modifications,
    /// view changes, and selection changes.
    /// </summary>
    public class ChangeTracker
    {
        private static ChangeTracker _instance;
        private static readonly object _lock = new object();

        private UIApplication _uiApp;
        private readonly List<ChangeRecord> _changeLog = new List<ChangeRecord>();
        private readonly int _maxLogSize = 1000;
        private ElementId[] _currentSelection = new ElementId[0];
        private string _currentViewName = "";
        private long _currentViewId = -1;
        private string _currentDocumentPath = "";
        private DateTime _lastChangeTime = DateTime.MinValue;

        public static ChangeTracker Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        if (_instance == null)
                        {
                            _instance = new ChangeTracker();
                        }
                    }
                }
                return _instance;
            }
        }

        private ChangeTracker() { }

        /// <summary>
        /// Initialize the change tracker with the UIApplication
        /// </summary>
        public void Initialize(UIApplication uiApp)
        {
            _uiApp = uiApp;

            // Subscribe to application-level events
            uiApp.Application.DocumentChanged += OnDocumentChanged;
            uiApp.Application.DocumentOpened += OnDocumentOpened;
            uiApp.Application.DocumentClosing += OnDocumentClosing;
            uiApp.Application.DocumentSaved += OnDocumentSaved;
            uiApp.Application.DocumentSavedAs += OnDocumentSavedAs;

            // Subscribe to UI events
            uiApp.ViewActivated += OnViewActivated;
            uiApp.SelectionChanged += OnSelectionChanged;

            // Log initialization
            AddChangeRecord(new ChangeRecord
            {
                Timestamp = DateTime.Now,
                ChangeType = ChangeType.SystemEvent,
                Description = "ChangeTracker initialized",
                Details = new Dictionary<string, object>
                {
                    { "version", "1.0.0" },
                    { "maxLogSize", _maxLogSize }
                }
            });

            Serilog.Log.Information("ChangeTracker initialized with all event handlers");
        }

        /// <summary>
        /// Shutdown and unsubscribe from all events
        /// </summary>
        public void Shutdown()
        {
            if (_uiApp != null)
            {
                _uiApp.Application.DocumentChanged -= OnDocumentChanged;
                _uiApp.Application.DocumentOpened -= OnDocumentOpened;
                _uiApp.Application.DocumentClosing -= OnDocumentClosing;
                _uiApp.Application.DocumentSaved -= OnDocumentSaved;
                _uiApp.Application.DocumentSavedAs -= OnDocumentSavedAs;
                _uiApp.ViewActivated -= OnViewActivated;
                _uiApp.SelectionChanged -= OnSelectionChanged;
            }

            Serilog.Log.Information("ChangeTracker shutdown");
        }

        #region Event Handlers

        private void OnDocumentChanged(object sender, DocumentChangedEventArgs e)
        {
            try
            {
                var doc = e.GetDocument();
                var addedIds = e.GetAddedElementIds();
                var deletedIds = e.GetDeletedElementIds();
                var modifiedIds = e.GetModifiedElementIds();
                var transactionNames = e.GetTransactionNames();

                string transactionName = transactionNames.Count > 0 ? string.Join(", ", transactionNames) : "Unknown";

                // Log added elements
                if (addedIds.Count > 0)
                {
                    var addedElements = new List<Dictionary<string, object>>();
                    foreach (var id in addedIds)
                    {
                        var elem = doc.GetElement(id);
                        if (elem != null)
                        {
                            addedElements.Add(new Dictionary<string, object>
                            {
                                { "id", id.Value },
                                { "category", elem.Category?.Name ?? "Unknown" },
                                { "name", elem.Name ?? "" },
                                { "typeName", GetTypeName(elem) }
                            });
                        }
                    }

                    AddChangeRecord(new ChangeRecord
                    {
                        Timestamp = DateTime.Now,
                        ChangeType = ChangeType.ElementsAdded,
                        Description = $"Added {addedIds.Count} element(s)",
                        TransactionName = transactionName,
                        DocumentName = doc.Title,
                        ElementCount = addedIds.Count,
                        Details = new Dictionary<string, object>
                        {
                            { "elements", addedElements },
                            { "elementIds", addedIds.Select(id => id.Value).ToList() }
                        }
                    }, doc);
                }

                // Log deleted elements
                if (deletedIds.Count > 0)
                {
                    AddChangeRecord(new ChangeRecord
                    {
                        Timestamp = DateTime.Now,
                        ChangeType = ChangeType.ElementsDeleted,
                        Description = $"Deleted {deletedIds.Count} element(s)",
                        TransactionName = transactionName,
                        DocumentName = doc.Title,
                        ElementCount = deletedIds.Count,
                        Details = new Dictionary<string, object>
                        {
                            { "elementIds", deletedIds.Select(id => id.Value).ToList() }
                        }
                    }, doc);
                }

                // Log modified elements
                if (modifiedIds.Count > 0)
                {
                    var modifiedElements = new List<Dictionary<string, object>>();
                    foreach (var id in modifiedIds)
                    {
                        var elem = doc.GetElement(id);
                        if (elem != null)
                        {
                            modifiedElements.Add(new Dictionary<string, object>
                            {
                                { "id", id.Value },
                                { "category", elem.Category?.Name ?? "Unknown" },
                                { "name", elem.Name ?? "" },
                                { "typeName", GetTypeName(elem) }
                            });
                        }
                    }

                    AddChangeRecord(new ChangeRecord
                    {
                        Timestamp = DateTime.Now,
                        ChangeType = ChangeType.ElementsModified,
                        Description = $"Modified {modifiedIds.Count} element(s)",
                        TransactionName = transactionName,
                        DocumentName = doc.Title,
                        ElementCount = modifiedIds.Count,
                        Details = new Dictionary<string, object>
                        {
                            { "elements", modifiedElements },
                            { "elementIds", modifiedIds.Select(id => id.Value).ToList() }
                        }
                    }, doc);
                }

                _lastChangeTime = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnDocumentChanged");
            }
        }

        private void OnViewActivated(object sender, ViewActivatedEventArgs e)
        {
            try
            {
                var currentView = e.CurrentActiveView;
                var previousView = e.PreviousActiveView;

                string previousViewName = previousView?.Name ?? "None";
                string currentViewName = currentView?.Name ?? "Unknown";

                _currentViewName = currentViewName;
                _currentViewId = currentView?.Id.Value ?? -1;

                var currentDoc = currentView?.Document;

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.ViewChanged,
                    Description = $"View changed: {previousViewName} -> {currentViewName}",
                    DocumentName = currentDoc?.Title ?? "",
                    Details = new Dictionary<string, object>
                    {
                        { "previousView", previousViewName },
                        { "previousViewId", previousView?.Id.Value ?? -1 },
                        { "currentView", currentViewName },
                        { "currentViewId", currentView?.Id.Value ?? -1 },
                        { "viewType", currentView?.ViewType.ToString() ?? "Unknown" },
                        { "isSheet", currentView is ViewSheet },
                        { "sheetNumber", (currentView as ViewSheet)?.SheetNumber ?? "" }
                    }
                }, currentDoc);

                // Learn from view for preferences
                if (currentView != null && currentDoc != null)
                {
                    PreferenceLearner.Instance.LearnFromView(currentView, currentDoc);
                }

                _lastChangeTime = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnViewActivated");
            }
        }

        private void OnSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            try
            {
                var doc = e.GetDocument();
                var selectedIds = e.GetSelectedElements();

                _currentSelection = selectedIds.ToArray();

                var selectedElements = new List<Dictionary<string, object>>();
                foreach (var id in selectedIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem != null)
                    {
                        selectedElements.Add(new Dictionary<string, object>
                        {
                            { "id", id.Value },
                            { "category", elem.Category?.Name ?? "Unknown" },
                            { "name", elem.Name ?? "" },
                            { "typeName", GetTypeName(elem) }
                        });
                    }
                }

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.SelectionChanged,
                    Description = $"Selection changed: {selectedIds.Count} element(s) selected",
                    DocumentName = doc.Title,
                    ElementCount = selectedIds.Count,
                    Details = new Dictionary<string, object>
                    {
                        { "elements", selectedElements },
                        { "elementIds", selectedIds.Select(id => id.Value).ToList() }
                    }
                }, doc);
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnSelectionChanged");
            }
        }

        private void OnDocumentOpened(object sender, DocumentOpenedEventArgs e)
        {
            try
            {
                var doc = e.Document;
                _currentDocumentPath = doc.PathName;

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.DocumentOpened,
                    Description = $"Document opened: {doc.Title}",
                    DocumentName = doc.Title,
                    Details = new Dictionary<string, object>
                    {
                        { "path", doc.PathName },
                        { "isWorkshared", doc.IsWorkshared }
                    }
                }, doc);

                _lastChangeTime = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnDocumentOpened");
            }
        }

        private void OnDocumentClosing(object sender, DocumentClosingEventArgs e)
        {
            try
            {
                var doc = e.Document;

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.DocumentClosing,
                    Description = $"Document closing: {doc.Title}",
                    DocumentName = doc.Title,
                    Details = new Dictionary<string, object>
                    {
                        { "path", doc.PathName }
                    }
                }, doc);
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnDocumentClosing");
            }
        }

        private void OnDocumentSaved(object sender, DocumentSavedEventArgs e)
        {
            try
            {
                var doc = e.Document;

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.DocumentSaved,
                    Description = $"Document saved: {doc.Title}",
                    DocumentName = doc.Title,
                    Details = new Dictionary<string, object>
                    {
                        { "path", doc.PathName }
                    }
                }, doc);

                _lastChangeTime = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnDocumentSaved");
            }
        }

        private void OnDocumentSavedAs(object sender, DocumentSavedAsEventArgs e)
        {
            try
            {
                var doc = e.Document;

                AddChangeRecord(new ChangeRecord
                {
                    Timestamp = DateTime.Now,
                    ChangeType = ChangeType.DocumentSaved,
                    Description = $"Document saved as: {doc.Title}",
                    DocumentName = doc.Title,
                    Details = new Dictionary<string, object>
                    {
                        { "path", doc.PathName },
                        { "originalPath", e.OriginalPath }
                    }
                }, doc);

                _lastChangeTime = DateTime.Now;
            }
            catch (Exception ex)
            {
                Serilog.Log.Error(ex, "Error in OnDocumentSavedAs");
            }
        }

        #endregion

        #region Helper Methods

        private string GetTypeName(Element elem)
        {
            try
            {
                var typeId = elem.GetTypeId();
                if (typeId != null && typeId != ElementId.InvalidElementId)
                {
                    var type = elem.Document.GetElement(typeId);
                    return type?.Name ?? "";
                }
            }
            catch { }
            return "";
        }

        private void AddChangeRecord(ChangeRecord record, Document doc = null)
        {
            lock (_changeLog)
            {
                _changeLog.Add(record);

                // Trim log if too large
                while (_changeLog.Count > _maxLogSize)
                {
                    _changeLog.RemoveAt(0);
                }
            }

            // Feed to intelligence system for learning
            try
            {
                if (doc == null && _uiApp?.ActiveUIDocument != null)
                {
                    doc = _uiApp.ActiveUIDocument.Document;
                }

                if (doc != null)
                {
                    // Feed to ProactiveAssistant for analysis and suggestions
                    ProactiveAssistant.Instance.ProcessChange(record, doc);
                }
            }
            catch (Exception ex)
            {
                Serilog.Log.Debug($"Error feeding to intelligence system: {ex.Message}");
            }
        }

        #endregion

        #region Public Query Methods

        /// <summary>
        /// Get all recent changes (last N records)
        /// </summary>
        public List<ChangeRecord> GetRecentChanges(int count = 50)
        {
            lock (_changeLog)
            {
                return _changeLog.Skip(Math.Max(0, _changeLog.Count - count)).ToList();
            }
        }

        /// <summary>
        /// Get changes since a specific timestamp
        /// </summary>
        public List<ChangeRecord> GetChangesSince(DateTime since)
        {
            lock (_changeLog)
            {
                return _changeLog.Where(c => c.Timestamp > since).ToList();
            }
        }

        /// <summary>
        /// Get changes of a specific type
        /// </summary>
        public List<ChangeRecord> GetChangesByType(ChangeType changeType, int count = 50)
        {
            lock (_changeLog)
            {
                return _changeLog.Where(c => c.ChangeType == changeType)
                    .Skip(Math.Max(0, _changeLog.Count(c => c.ChangeType == changeType) - count))
                    .ToList();
            }
        }

        /// <summary>
        /// Get current selection
        /// </summary>
        public ElementId[] GetCurrentSelection()
        {
            return _currentSelection;
        }

        /// <summary>
        /// Get current view info
        /// </summary>
        public (string name, long id) GetCurrentViewInfo()
        {
            return (_currentViewName, _currentViewId);
        }

        /// <summary>
        /// Get last change time
        /// </summary>
        public DateTime GetLastChangeTime()
        {
            return _lastChangeTime;
        }

        /// <summary>
        /// Get change log statistics
        /// </summary>
        public Dictionary<string, int> GetStatistics()
        {
            lock (_changeLog)
            {
                return _changeLog.GroupBy(c => c.ChangeType.ToString())
                    .ToDictionary(g => g.Key, g => g.Count());
            }
        }

        /// <summary>
        /// Clear the change log
        /// </summary>
        public void ClearLog()
        {
            lock (_changeLog)
            {
                _changeLog.Clear();
            }
        }

        #endregion
    }

    /// <summary>
    /// Types of changes that can be tracked
    /// </summary>
    public enum ChangeType
    {
        ElementsAdded,
        ElementsDeleted,
        ElementsModified,
        ViewChanged,
        SelectionChanged,
        DocumentOpened,
        DocumentClosing,
        DocumentSaved,
        SystemEvent
    }

    /// <summary>
    /// Record of a single change event
    /// </summary>
    public class ChangeRecord
    {
        public DateTime Timestamp { get; set; }
        public ChangeType ChangeType { get; set; }
        public string Description { get; set; }
        public string TransactionName { get; set; }
        public string DocumentName { get; set; }
        public int ElementCount { get; set; }
        public Dictionary<string, object> Details { get; set; }

        public ChangeRecord()
        {
            Details = new Dictionary<string, object>();
        }
    }
}

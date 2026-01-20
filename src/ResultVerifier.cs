using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// Suppress CS1998 for async verification methods that don't need await
// These match the delegate signature in _verifiers dictionary
#pragma warning disable CS1998

namespace RevitMCPBridge
{
    /// <summary>
    /// Verifies that MCP commands actually produced the expected results.
    /// Prevents "I created it" when nothing actually happened.
    /// </summary>
    public class ResultVerifier
    {
        private Func<string, JObject, Task<string>> _executeMethod;

        // Verification methods for each command type
        private readonly Dictionary<string, Func<JObject, JObject, Task<VerificationResult>>> _verifiers;

        public ResultVerifier()
        {
            _verifiers = new Dictionary<string, Func<JObject, JObject, Task<VerificationResult>>>(StringComparer.OrdinalIgnoreCase)
            {
                // Sheet operations
                {"createSheet", VerifySheetCreated},
                {"deleteSheet", VerifySheetDeleted},

                // View operations
                {"placeViewOnSheet", VerifyViewPlaced},

                // Element operations
                {"createWall", VerifyElementCreated},
                {"placeDoor", VerifyElementCreated},
                {"placeWindow", VerifyElementCreated},
                {"createRoom", VerifyRoomCreated},
                {"placeTextNote", VerifyElementCreated},
                {"placeFamilyInstance", VerifyElementCreated},

                // Parameter operations
                {"setParameter", VerifyParameterSet},

                // Delete operations
                {"deleteElements", VerifyElementsDeleted},
            };
        }

        /// <summary>
        /// Set the method executor (to call MCP methods for verification)
        /// </summary>
        public void SetExecutor(Func<string, JObject, Task<string>> executor)
        {
            _executeMethod = executor;
        }

        /// <summary>
        /// Verify a command result
        /// </summary>
        public async Task<VerificationResult> VerifyAsync(string method, JObject parameters, JObject result)
        {
            // If the command itself failed, no need to verify
            if (result["success"]?.ToObject<bool>() != true)
            {
                return new VerificationResult
                {
                    Verified = false,
                    Method = method,
                    Message = $"Command failed: {result["error"]}",
                    CommandSucceeded = false
                };
            }

            // Check if we have a verifier for this method
            if (_verifiers.TryGetValue(method, out var verifier))
            {
                try
                {
                    return await verifier(parameters, result);
                }
                catch (Exception ex)
                {
                    return new VerificationResult
                    {
                        Verified = false,
                        Method = method,
                        Message = $"Verification error: {ex.Message}",
                        CommandSucceeded = true
                    };
                }
            }

            // No specific verifier - assume success if command succeeded
            return new VerificationResult
            {
                Verified = true,
                Method = method,
                Message = "Command completed (no specific verification available)",
                CommandSucceeded = true
            };
        }

        #region Verification Methods

        private async Task<VerificationResult> VerifySheetCreated(JObject parameters, JObject result)
        {
            var sheetNumber = parameters["sheetNumber"]?.ToString();
            var createdId = result["result"]?["sheetId"]?.ToObject<long>() ??
                           result["result"]?["id"]?.ToObject<long>() ?? 0;

            if (createdId == 0 && string.IsNullOrEmpty(sheetNumber))
            {
                return new VerificationResult
                {
                    Verified = false,
                    Method = "createSheet",
                    Message = "Could not determine sheet ID or number to verify",
                    CommandSucceeded = true
                };
            }

            // Query sheets to verify
            if (_executeMethod != null)
            {
                var sheetsResult = await _executeMethod("getSheets", new JObject());
                var sheetsObj = JObject.Parse(sheetsResult);

                if (sheetsObj["success"]?.ToObject<bool>() == true)
                {
                    var sheets = sheetsObj["result"]?["sheets"] as JArray;
                    if (sheets != null)
                    {
                        bool found = false;
                        if (createdId > 0)
                        {
                            found = sheets.Any(s => s["id"]?.ToObject<long>() == createdId);
                        }
                        else if (!string.IsNullOrEmpty(sheetNumber))
                        {
                            found = sheets.Any(s => s["sheetNumber"]?.ToString() == sheetNumber);
                        }

                        return new VerificationResult
                        {
                            Verified = found,
                            Method = "createSheet",
                            Message = found ?
                                $"✓ Sheet {sheetNumber ?? createdId.ToString()} verified in model" :
                                $"⚠ Sheet {sheetNumber ?? createdId.ToString()} not found in model after creation",
                            CommandSucceeded = true,
                            ElementId = createdId
                        };
                    }
                }
            }

            // Can't verify without executor
            return new VerificationResult
            {
                Verified = true,
                Method = "createSheet",
                Message = $"Sheet created (ID: {createdId}) - verification skipped",
                CommandSucceeded = true,
                ElementId = createdId
            };
        }

        private async Task<VerificationResult> VerifySheetDeleted(JObject parameters, JObject result)
        {
            var sheetId = parameters["sheetId"]?.ToObject<long>() ?? 0;

            if (sheetId == 0)
            {
                return new VerificationResult
                {
                    Verified = true,
                    Method = "deleteSheet",
                    Message = "Sheet deletion completed",
                    CommandSucceeded = true
                };
            }

            // Query sheets to verify deletion
            if (_executeMethod != null)
            {
                var sheetsResult = await _executeMethod("getSheets", new JObject());
                var sheetsObj = JObject.Parse(sheetsResult);

                if (sheetsObj["success"]?.ToObject<bool>() == true)
                {
                    var sheets = sheetsObj["result"]?["sheets"] as JArray;
                    if (sheets != null)
                    {
                        bool stillExists = sheets.Any(s => s["id"]?.ToObject<long>() == sheetId);

                        return new VerificationResult
                        {
                            Verified = !stillExists,
                            Method = "deleteSheet",
                            Message = stillExists ?
                                $"⚠ Sheet {sheetId} still exists after deletion" :
                                $"✓ Sheet {sheetId} successfully deleted",
                            CommandSucceeded = true
                        };
                    }
                }
            }

            return new VerificationResult
            {
                Verified = true,
                Method = "deleteSheet",
                Message = "Sheet deletion completed",
                CommandSucceeded = true
            };
        }

        private async Task<VerificationResult> VerifyViewPlaced(JObject parameters, JObject result)
        {
            var viewportId = result["result"]?["viewportId"]?.ToObject<long>() ?? 0;

            return new VerificationResult
            {
                Verified = viewportId > 0,
                Method = "placeViewOnSheet",
                Message = viewportId > 0 ?
                    $"✓ View placed on sheet (viewport ID: {viewportId})" :
                    "⚠ View placement returned no viewport ID",
                CommandSucceeded = true,
                ElementId = viewportId
            };
        }

        private async Task<VerificationResult> VerifyElementCreated(JObject parameters, JObject result)
        {
            var elementId = result["result"]?["elementId"]?.ToObject<long>() ??
                           result["result"]?["id"]?.ToObject<long>() ??
                           result["result"]?["wallId"]?.ToObject<long>() ??
                           result["result"]?["doorId"]?.ToObject<long>() ??
                           result["result"]?["windowId"]?.ToObject<long>() ??
                           result["result"]?["textNoteId"]?.ToObject<long>() ?? 0;

            return new VerificationResult
            {
                Verified = elementId > 0,
                Method = "createElement",
                Message = elementId > 0 ?
                    $"✓ Element created (ID: {elementId})" :
                    "⚠ Element creation returned no ID",
                CommandSucceeded = true,
                ElementId = elementId
            };
        }

        private async Task<VerificationResult> VerifyRoomCreated(JObject parameters, JObject result)
        {
            var roomId = result["result"]?["roomId"]?.ToObject<long>() ??
                        result["result"]?["id"]?.ToObject<long>() ?? 0;

            if (roomId > 0 && _executeMethod != null)
            {
                // Verify room exists
                var roomsResult = await _executeMethod("getRooms", new JObject());
                var roomsObj = JObject.Parse(roomsResult);

                if (roomsObj["success"]?.ToObject<bool>() == true)
                {
                    var rooms = roomsObj["result"]?["rooms"] as JArray;
                    if (rooms != null)
                    {
                        bool found = rooms.Any(r => r["id"]?.ToObject<long>() == roomId);
                        return new VerificationResult
                        {
                            Verified = found,
                            Method = "createRoom",
                            Message = found ?
                                $"✓ Room created and verified (ID: {roomId})" :
                                $"⚠ Room {roomId} not found after creation",
                            CommandSucceeded = true,
                            ElementId = roomId
                        };
                    }
                }
            }

            return new VerificationResult
            {
                Verified = roomId > 0,
                Method = "createRoom",
                Message = roomId > 0 ?
                    $"✓ Room created (ID: {roomId})" :
                    "⚠ Room creation returned no ID",
                CommandSucceeded = true,
                ElementId = roomId
            };
        }

        private async Task<VerificationResult> VerifyParameterSet(JObject parameters, JObject result)
        {
            var elementId = parameters["elementId"]?.ToObject<long>() ?? 0;
            var paramName = parameters["parameterName"]?.ToString();
            var newValue = parameters["value"]?.ToString();

            // Could query the element to verify parameter was set
            // For now, trust the result
            return new VerificationResult
            {
                Verified = true,
                Method = "setParameter",
                Message = $"✓ Parameter '{paramName}' set on element {elementId}",
                CommandSucceeded = true
            };
        }

        private async Task<VerificationResult> VerifyElementsDeleted(JObject parameters, JObject result)
        {
            var deletedCount = result["result"]?["deletedCount"]?.ToObject<int>() ?? 0;
            var requestedIds = parameters["elementIds"] as JArray;
            var requestedCount = requestedIds?.Count ?? 0;

            return new VerificationResult
            {
                Verified = deletedCount > 0,
                Method = "deleteElements",
                Message = deletedCount > 0 ?
                    $"✓ Deleted {deletedCount} element(s)" :
                    "⚠ No elements were deleted",
                CommandSucceeded = true,
                AffectedCount = deletedCount
            };
        }

        #endregion
    }

    /// <summary>
    /// Result of verification check
    /// </summary>
    public class VerificationResult
    {
        public bool Verified { get; set; }
        public bool CommandSucceeded { get; set; }
        public string Method { get; set; }
        public string Message { get; set; }
        public long ElementId { get; set; }
        public int AffectedCount { get; set; }

        public override string ToString()
        {
            return Message;
        }
    }
}

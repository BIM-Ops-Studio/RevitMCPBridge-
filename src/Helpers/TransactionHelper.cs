using System;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using Serilog;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Helper utilities for transaction management in Revit.
    /// Reduces boilerplate for transaction handling across all methods.
    /// </summary>
    public static class TransactionHelper
    {
        /// <summary>
        /// Execute an action within a transaction, returning JSON result.
        /// Handles all transaction lifecycle: start, commit/rollback, error handling.
        /// </summary>
        /// <typeparam name="T">Return type for success result</typeparam>
        /// <param name="doc">Revit document</param>
        /// <param name="transactionName">Name for the transaction</param>
        /// <param name="action">Action to execute within transaction</param>
        /// <returns>JSON string with success/error result</returns>
        public static string Execute<T>(Document doc, string transactionName, Func<Transaction, T> action)
        {
            if (doc == null)
            {
                return ResponseBuilder.Error("No document is open").Build();
            }

            using (var trans = new Transaction(doc, transactionName))
            {
                try
                {
                    trans.Start();
                    var result = action(trans);
                    trans.Commit();

                    return ResponseBuilder.Success()
                        .With("result", result)
                        .Build();
                }
                catch (Exception ex)
                {
                    if (trans.HasStarted() && !trans.HasEnded())
                    {
                        trans.RollBack();
                    }

                    Log.Error(ex, "Transaction '{TransactionName}' failed", transactionName);
                    return ResponseBuilder.FromException(ex).Build();
                }
            }
        }

        /// <summary>
        /// Execute an action within a transaction that returns void.
        /// </summary>
        public static string Execute(Document doc, string transactionName, Action<Transaction> action)
        {
            return Execute(doc, transactionName, (trans) =>
            {
                action(trans);
                return new { completed = true };
            });
        }

        /// <summary>
        /// Execute a read-only operation (no transaction needed).
        /// </summary>
        public static string ExecuteReadOnly<T>(Document doc, Func<T> action, string operationName = null)
        {
            if (doc == null)
            {
                return ResponseBuilder.Error("No document is open").Build();
            }

            try
            {
                var result = action();

                return ResponseBuilder.Success()
                    .With("result", result)
                    .Build();
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Read operation '{Operation}' failed", operationName ?? "unknown");
                return ResponseBuilder.FromException(ex).Build();
            }
        }

        /// <summary>
        /// Execute with UIApplication context
        /// </summary>
        public static string ExecuteWithUIApp(UIApplication uiApp, string transactionName,
            Func<UIApplication, Document, Transaction, object> action)
        {
            var doc = uiApp?.ActiveUIDocument?.Document;
            if (doc == null)
            {
                return ResponseBuilder.Error("No document is open").Build();
            }

            using (var trans = new Transaction(doc, transactionName))
            {
                try
                {
                    trans.Start();
                    var result = action(uiApp, doc, trans);
                    trans.Commit();

                    return ResponseBuilder.Success()
                        .With("result", result)
                        .Build();
                }
                catch (Exception ex)
                {
                    if (trans.HasStarted() && !trans.HasEnded())
                    {
                        trans.RollBack();
                    }

                    Log.Error(ex, "Transaction '{TransactionName}' failed", transactionName);
                    return ResponseBuilder.FromException(ex).Build();
                }
            }
        }

        /// <summary>
        /// Execute with sub-transactions for complex operations
        /// </summary>
        public static string ExecuteWithSubTransactions(Document doc, string transactionName,
            Func<TransactionGroup, object> action)
        {
            if (doc == null)
            {
                return ResponseBuilder.Error("No document is open").Build();
            }

            using (var group = new TransactionGroup(doc, transactionName))
            {
                try
                {
                    group.Start();
                    var result = action(group);
                    group.Assimilate();

                    return ResponseBuilder.Success()
                        .With("result", result)
                        .Build();
                }
                catch (Exception ex)
                {
                    if (group.HasStarted())
                    {
                        group.RollBack();
                    }

                    Log.Error(ex, "Transaction group '{TransactionName}' failed", transactionName);
                    return ResponseBuilder.FromException(ex).Build();
                }
            }
        }
    }
}

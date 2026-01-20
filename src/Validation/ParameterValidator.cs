using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using RevitMCPBridge.Exceptions;

namespace RevitMCPBridge.Validation
{
    /// <summary>
    /// Fluent parameter validation for MCP method parameters.
    /// Provides chainable validation with descriptive error messages.
    /// </summary>
    public class ParameterValidator
    {
        private readonly JObject _parameters;
        private readonly List<string> _errors;
        private readonly string _methodName;

        public ParameterValidator(JObject parameters, string methodName = null)
        {
            _parameters = parameters ?? new JObject();
            _errors = new List<string>();
            _methodName = methodName;
        }

        /// <summary>
        /// Start validation chain for a parameter
        /// </summary>
        public ParameterValidation Require(string parameterName)
        {
            return new ParameterValidation(this, parameterName, _parameters[parameterName], true);
        }

        /// <summary>
        /// Start validation chain for an optional parameter
        /// </summary>
        public ParameterValidation Optional(string parameterName)
        {
            return new ParameterValidation(this, parameterName, _parameters[parameterName], false);
        }

        /// <summary>
        /// Get a required value or throw
        /// </summary>
        public T GetRequired<T>(string parameterName)
        {
            var token = _parameters[parameterName];
            if (token == null)
                throw MCPValidationException.Required(parameterName);

            try
            {
                return token.Value<T>();
            }
            catch
            {
                throw MCPValidationException.InvalidType(parameterName, typeof(T).Name, token);
            }
        }

        /// <summary>
        /// Get an optional value with default
        /// </summary>
        public T GetOptional<T>(string parameterName, T defaultValue = default)
        {
            var token = _parameters[parameterName];
            if (token == null)
                return defaultValue;

            try
            {
                return token.Value<T>();
            }
            catch
            {
                return defaultValue;
            }
        }

        /// <summary>
        /// Get a required integer element ID
        /// </summary>
        public int GetElementId(string parameterName)
        {
            var id = GetRequired<int>(parameterName);
            if (id <= 0)
                throw new MCPValidationException(parameterName, $"Element ID must be positive, got {id}", id);
            return id;
        }

        /// <summary>
        /// Get an optional integer element ID
        /// </summary>
        public int? GetOptionalElementId(string parameterName)
        {
            var token = _parameters[parameterName];
            if (token == null)
                return null;

            var id = token.Value<int>();
            if (id <= 0)
                return null;
            return id;
        }

        /// <summary>
        /// Get a required positive double value
        /// </summary>
        public double GetPositiveDouble(string parameterName)
        {
            var value = GetRequired<double>(parameterName);
            if (value <= 0)
                throw MCPValidationException.OutOfRange(parameterName, value, 0, "∞");
            return value;
        }

        /// <summary>
        /// Get coordinates (x, y, optional z)
        /// </summary>
        public (double x, double y, double z) GetCoordinates(string prefix = "")
        {
            var xName = string.IsNullOrEmpty(prefix) ? "x" : $"{prefix}X";
            var yName = string.IsNullOrEmpty(prefix) ? "y" : $"{prefix}Y";
            var zName = string.IsNullOrEmpty(prefix) ? "z" : $"{prefix}Z";

            var x = GetRequired<double>(xName);
            var y = GetRequired<double>(yName);
            var z = GetOptional<double>(zName, 0.0);

            return (x, y, z);
        }

        /// <summary>
        /// Get start/end coordinates for line-based elements
        /// </summary>
        public ((double x, double y, double z) start, (double x, double y, double z) end) GetLineCoordinates()
        {
            var startX = GetRequired<double>("startX");
            var startY = GetRequired<double>("startY");
            var startZ = GetOptional<double>("startZ", 0.0);
            var endX = GetRequired<double>("endX");
            var endY = GetRequired<double>("endY");
            var endZ = GetOptional<double>("endZ", 0.0);

            return ((startX, startY, startZ), (endX, endY, endZ));
        }

        /// <summary>
        /// Validate that line has non-zero length
        /// </summary>
        public void ValidateNonZeroLength(double startX, double startY, double endX, double endY)
        {
            var length = Math.Sqrt(Math.Pow(endX - startX, 2) + Math.Pow(endY - startY, 2));
            if (length < 0.001) // Less than 0.001 feet = essentially zero
            {
                throw MCPRevitException.InvalidGeometry("Line must have non-zero length");
            }
        }

        internal void AddError(string error)
        {
            _errors.Add(error);
        }

        /// <summary>
        /// Throw if any validation errors accumulated
        /// </summary>
        public void ThrowIfInvalid()
        {
            if (_errors.Count > 0)
            {
                var message = string.Join("; ", _errors);
                throw new MCPValidationException("parameters", message);
            }
        }
    }

    /// <summary>
    /// Fluent validation chain for a single parameter
    /// </summary>
    public class ParameterValidation
    {
        private readonly ParameterValidator _validator;
        private readonly string _parameterName;
        private readonly JToken _value;
        private readonly bool _required;
        private bool _isValid = true;

        internal ParameterValidation(ParameterValidator validator, string parameterName, JToken value, bool required)
        {
            _validator = validator;
            _parameterName = parameterName;
            _value = value;
            _required = required;

            // Check required
            if (required && value == null)
            {
                _validator.AddError($"'{parameterName}' is required");
                _isValid = false;
            }
        }

        /// <summary>
        /// Validate value is of expected type
        /// </summary>
        public ParameterValidation IsType<T>()
        {
            if (!_isValid || _value == null) return this;

            try
            {
                _value.Value<T>();
            }
            catch
            {
                _validator.AddError($"'{_parameterName}' must be of type {typeof(T).Name}");
                _isValid = false;
            }
            return this;
        }

        /// <summary>
        /// Validate numeric value is in range
        /// </summary>
        public ParameterValidation InRange(double min, double max)
        {
            if (!_isValid || _value == null) return this;

            try
            {
                var val = _value.Value<double>();
                if (val < min || val > max)
                {
                    _validator.AddError($"'{_parameterName}' must be between {min} and {max}");
                    _isValid = false;
                }
            }
            catch { }
            return this;
        }

        /// <summary>
        /// Validate numeric value is positive
        /// </summary>
        public ParameterValidation IsPositive()
        {
            if (!_isValid || _value == null) return this;

            try
            {
                var val = _value.Value<double>();
                if (val <= 0)
                {
                    _validator.AddError($"'{_parameterName}' must be positive");
                    _isValid = false;
                }
            }
            catch { }
            return this;
        }

        /// <summary>
        /// Validate string is not empty
        /// </summary>
        public ParameterValidation NotEmpty()
        {
            if (!_isValid || _value == null) return this;

            var str = _value.Value<string>();
            if (string.IsNullOrWhiteSpace(str))
            {
                _validator.AddError($"'{_parameterName}' cannot be empty");
                _isValid = false;
            }
            return this;
        }

        /// <summary>
        /// Validate string matches pattern
        /// </summary>
        public ParameterValidation Matches(string pattern, string patternDescription = null)
        {
            if (!_isValid || _value == null) return this;

            var str = _value.Value<string>();
            if (!System.Text.RegularExpressions.Regex.IsMatch(str ?? "", pattern))
            {
                var desc = patternDescription ?? pattern;
                _validator.AddError($"'{_parameterName}' must match pattern: {desc}");
                _isValid = false;
            }
            return this;
        }

        /// <summary>
        /// Validate value is one of allowed values
        /// </summary>
        public ParameterValidation OneOf(params string[] allowedValues)
        {
            if (!_isValid || _value == null) return this;

            var str = _value.Value<string>();
            var found = false;
            foreach (var allowed in allowedValues)
            {
                if (string.Equals(str, allowed, StringComparison.OrdinalIgnoreCase))
                {
                    found = true;
                    break;
                }
            }

            if (!found)
            {
                _validator.AddError($"'{_parameterName}' must be one of: {string.Join(", ", allowedValues)}");
                _isValid = false;
            }
            return this;
        }

        /// <summary>
        /// Chain back to validator
        /// </summary>
        public ParameterValidator And => _validator;
    }
}

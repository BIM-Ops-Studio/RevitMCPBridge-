using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;

namespace RevitMCPBridge.Helpers
{
    /// <summary>
    /// Helper utilities for geometry calculations and conversions.
    /// </summary>
    public static class GeometryHelper
    {
        #region Unit Conversions

        /// <summary>
        /// Convert feet to millimeters.
        /// </summary>
        public static double FeetToMm(double feet)
        {
            return feet * 304.8;
        }

        /// <summary>
        /// Convert millimeters to feet.
        /// </summary>
        public static double MmToFeet(double mm)
        {
            return mm / 304.8;
        }

        /// <summary>
        /// Convert feet to inches.
        /// </summary>
        public static double FeetToInches(double feet)
        {
            return feet * 12.0;
        }

        /// <summary>
        /// Convert inches to feet.
        /// </summary>
        public static double InchesToFeet(double inches)
        {
            return inches / 12.0;
        }

        /// <summary>
        /// Convert feet to meters.
        /// </summary>
        public static double FeetToMeters(double feet)
        {
            return feet * 0.3048;
        }

        /// <summary>
        /// Convert meters to feet.
        /// </summary>
        public static double MetersToFeet(double meters)
        {
            return meters / 0.3048;
        }

        /// <summary>
        /// Convert degrees to radians.
        /// </summary>
        public static double DegreesToRadians(double degrees)
        {
            return degrees * Math.PI / 180.0;
        }

        /// <summary>
        /// Convert radians to degrees.
        /// </summary>
        public static double RadiansToDegrees(double radians)
        {
            return radians * 180.0 / Math.PI;
        }

        #endregion

        #region Point/Vector Creation

        /// <summary>
        /// Create an XYZ point from coordinates.
        /// </summary>
        public static XYZ CreatePoint(double x, double y, double z = 0)
        {
            return new XYZ(x, y, z);
        }

        /// <summary>
        /// Create an XYZ point from a tuple.
        /// </summary>
        public static XYZ CreatePoint((double x, double y, double z) coords)
        {
            return new XYZ(coords.x, coords.y, coords.z);
        }

        /// <summary>
        /// Create a normalized direction vector.
        /// </summary>
        public static XYZ CreateDirection(double x, double y, double z = 0)
        {
            var dir = new XYZ(x, y, z);
            return dir.Normalize();
        }

        #endregion

        #region Line/Curve Creation

        /// <summary>
        /// Create a line from start and end points.
        /// </summary>
        public static Line CreateLine(double startX, double startY, double endX, double endY, double z = 0)
        {
            var start = new XYZ(startX, startY, z);
            var end = new XYZ(endX, endY, z);
            return Line.CreateBound(start, end);
        }

        /// <summary>
        /// Create a line from XYZ points.
        /// </summary>
        public static Line CreateLine(XYZ start, XYZ end)
        {
            return Line.CreateBound(start, end);
        }

        /// <summary>
        /// Create a horizontal line at a specific elevation.
        /// </summary>
        public static Line CreateHorizontalLine(double startX, double startY, double endX, double endY, double elevation = 0)
        {
            return CreateLine(startX, startY, endX, endY, elevation);
        }

        #endregion

        #region Distance Calculations

        /// <summary>
        /// Calculate 2D distance between two points.
        /// </summary>
        public static double Distance2D(double x1, double y1, double x2, double y2)
        {
            return Math.Sqrt(Math.Pow(x2 - x1, 2) + Math.Pow(y2 - y1, 2));
        }

        /// <summary>
        /// Calculate 3D distance between two XYZ points.
        /// </summary>
        public static double Distance3D(XYZ p1, XYZ p2)
        {
            return p1.DistanceTo(p2);
        }

        /// <summary>
        /// Calculate the length of a line.
        /// </summary>
        public static double LineLength(double startX, double startY, double endX, double endY)
        {
            return Distance2D(startX, startY, endX, endY);
        }

        /// <summary>
        /// Check if a line has zero or near-zero length.
        /// </summary>
        public static bool IsZeroLength(double startX, double startY, double endX, double endY, double tolerance = 0.001)
        {
            return LineLength(startX, startY, endX, endY) < tolerance;
        }

        #endregion

        #region Angle Calculations

        /// <summary>
        /// Calculate angle from start to end point (in radians).
        /// </summary>
        public static double AngleFromPoints(double startX, double startY, double endX, double endY)
        {
            return Math.Atan2(endY - startY, endX - startX);
        }

        /// <summary>
        /// Calculate angle between two vectors.
        /// </summary>
        public static double AngleBetweenVectors(XYZ v1, XYZ v2)
        {
            return v1.AngleTo(v2);
        }

        #endregion

        #region Bounding Box

        /// <summary>
        /// Get bounding box center point.
        /// </summary>
        public static XYZ GetBoundingBoxCenter(BoundingBoxXYZ box)
        {
            return (box.Min + box.Max) / 2;
        }

        /// <summary>
        /// Get bounding box dimensions.
        /// </summary>
        public static (double width, double height, double depth) GetBoundingBoxDimensions(BoundingBoxXYZ box)
        {
            var diff = box.Max - box.Min;
            return (diff.X, diff.Y, diff.Z);
        }

        /// <summary>
        /// Create a bounding box from min/max points.
        /// </summary>
        public static BoundingBoxXYZ CreateBoundingBox(XYZ min, XYZ max)
        {
            var box = new BoundingBoxXYZ();
            box.Min = min;
            box.Max = max;
            return box;
        }

        #endregion

        #region Polyline/Polygon

        /// <summary>
        /// Calculate the perimeter of a polygon.
        /// </summary>
        public static double CalculatePerimeter(IList<XYZ> points, bool closed = true)
        {
            double perimeter = 0;
            for (int i = 0; i < points.Count - 1; i++)
            {
                perimeter += points[i].DistanceTo(points[i + 1]);
            }

            if (closed && points.Count > 1)
            {
                perimeter += points[points.Count - 1].DistanceTo(points[0]);
            }

            return perimeter;
        }

        /// <summary>
        /// Calculate the 2D area of a polygon using the Shoelace formula.
        /// </summary>
        public static double CalculateArea(IList<XYZ> points)
        {
            double area = 0;
            int n = points.Count;

            for (int i = 0; i < n; i++)
            {
                int j = (i + 1) % n;
                area += points[i].X * points[j].Y;
                area -= points[j].X * points[i].Y;
            }

            return Math.Abs(area) / 2;
        }

        /// <summary>
        /// Get the centroid of a polygon.
        /// </summary>
        public static XYZ CalculateCentroid(IList<XYZ> points)
        {
            double x = points.Average(p => p.X);
            double y = points.Average(p => p.Y);
            double z = points.Average(p => p.Z);
            return new XYZ(x, y, z);
        }

        #endregion

        #region Transformations

        /// <summary>
        /// Rotate a point around the origin by angle (radians).
        /// </summary>
        public static XYZ RotatePoint(XYZ point, double angleRadians)
        {
            double cos = Math.Cos(angleRadians);
            double sin = Math.Sin(angleRadians);

            return new XYZ(
                point.X * cos - point.Y * sin,
                point.X * sin + point.Y * cos,
                point.Z
            );
        }

        /// <summary>
        /// Rotate a point around a center point by angle (radians).
        /// </summary>
        public static XYZ RotatePointAround(XYZ point, XYZ center, double angleRadians)
        {
            var translated = point - center;
            var rotated = RotatePoint(translated, angleRadians);
            return rotated + center;
        }

        /// <summary>
        /// Create a rotation transform around Z axis.
        /// </summary>
        public static Transform CreateRotationZ(XYZ origin, double angleRadians)
        {
            return Transform.CreateRotationAtPoint(XYZ.BasisZ, angleRadians, origin);
        }

        #endregion
    }
}

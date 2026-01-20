"""
Detail Library Text Standardization Script
==========================================
Batch processes all RVT detail files to standardize text:
- Font: Arial
- Size: 3/32" (0.09375")
- All text converted to UPPERCASE
- Single consistent text type across all files

Run this script in Revit via:
- pyRevit Script Editor
- RevitPythonShell
- Or integrate into RevitMCPBridge as a batch command

Author: Claude Code
Date: 2024-12-30
"""

import clr
import os
import sys
import datetime

# Add Revit API references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('RevitServices')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Collections.Generic import List

# Configuration
CONFIG = {
    "library_path": r"D:\Revit Detail Libraries\Revit Details",
    "text_type_name": '3/32" ARIAL NOTES',
    "font_name": "Arial",
    "text_size_inches": 0.09375,  # 3/32"
    "bold": False,
    "italic": False,
    "underline": False,
    "log_file": r"D:\RevitMCPBridge2026\logs\text_standardization.log",
    "dry_run": False,  # Set to True to preview without saving
}


def log_message(message, log_file=None):
    """Log message to console and optionally to file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            with open(log_file, 'a') as f:
                f.write(log_entry + "\n")
        except:
            pass


def get_all_rvt_files(library_path):
    """Recursively get all RVT files from library folder."""
    rvt_files = []
    for root, dirs, files in os.walk(library_path):
        for file in files:
            if file.lower().endswith('.rvt'):
                rvt_files.append(os.path.join(root, file))
    return sorted(rvt_files)


def get_or_create_text_type(doc, type_name, font_name, text_size_feet, bold=False):
    """Get existing text type or create a new one with specified parameters."""

    # Find existing text types
    collector = FilteredElementCollector(doc).OfClass(TextNoteType)

    # Check if our type already exists
    for text_type in collector:
        if text_type.Name == type_name:
            log_message(f"  Found existing text type: {type_name}")
            return text_type

    # Need to create new type - duplicate from first available
    existing_types = list(collector)
    if not existing_types:
        log_message("  ERROR: No text types found in document")
        return None

    # Duplicate the first text type
    source_type = existing_types[0]
    new_type = source_type.Duplicate(type_name)

    # Set parameters
    try:
        # Text Font parameter
        font_param = new_type.get_Parameter(BuiltInParameter.TEXT_FONT)
        if font_param and not font_param.IsReadOnly:
            font_param.Set(font_name)

        # Text Size parameter (in feet)
        size_param = new_type.get_Parameter(BuiltInParameter.TEXT_SIZE)
        if size_param and not size_param.IsReadOnly:
            size_param.Set(text_size_feet)

        # Bold parameter
        bold_param = new_type.get_Parameter(BuiltInParameter.TEXT_STYLE_BOLD)
        if bold_param and not bold_param.IsReadOnly:
            bold_param.Set(1 if bold else 0)

        # Italic parameter
        italic_param = new_type.get_Parameter(BuiltInParameter.TEXT_STYLE_ITALIC)
        if italic_param and not italic_param.IsReadOnly:
            italic_param.Set(0)

        # Underline parameter
        underline_param = new_type.get_Parameter(BuiltInParameter.TEXT_STYLE_UNDERLINE)
        if underline_param and not underline_param.IsReadOnly:
            underline_param.Set(0)

        log_message(f"  Created new text type: {type_name}")

    except Exception as ex:
        log_message(f"  Warning: Could not set all parameters: {str(ex)}")

    return new_type


def standardize_text_in_document(doc, target_type):
    """Change all TextNote elements to use the target type and convert to uppercase."""

    # Get all TextNote elements
    collector = FilteredElementCollector(doc).OfClass(TextNote)
    text_notes = list(collector)

    if not text_notes:
        log_message("  No text notes found in document")
        return 0, 0

    changed_count = 0
    uppercase_count = 0
    target_type_id = target_type.Id

    for text_note in text_notes:
        try:
            # Change type if different
            if text_note.GetTypeId() != target_type_id:
                text_note.ChangeTypeId(target_type_id)
                changed_count += 1

            # Convert text to uppercase
            current_text = text_note.Text
            if current_text:
                upper_text = current_text.upper()
                if upper_text != current_text:
                    text_note.Text = upper_text
                    uppercase_count += 1

        except Exception as ex:
            log_message(f"  Warning: Could not process text note {text_note.Id}: {str(ex)}")

    return changed_count, uppercase_count


def process_single_file(app, file_path, config):
    """Process a single RVT file."""

    file_name = os.path.basename(file_path)
    log_message(f"Processing: {file_name}")

    try:
        # Open the document
        open_options = OpenOptions()
        open_options.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets

        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
        doc = app.OpenDocumentFile(model_path, open_options)

        if doc is None:
            log_message(f"  ERROR: Could not open file")
            return False

        # Convert inches to feet for Revit API
        text_size_feet = config["text_size_inches"] / 12.0

        # Start transaction
        with Transaction(doc, "Standardize Text") as trans:
            trans.Start()

            # Get or create the standard text type
            target_type = get_or_create_text_type(
                doc,
                config["text_type_name"],
                config["font_name"],
                text_size_feet,
                config["bold"]
            )

            if target_type is None:
                trans.RollBack()
                doc.Close(False)
                return False

            # Standardize all text
            type_changes, case_changes = standardize_text_in_document(doc, target_type)

            trans.Commit()

        log_message(f"  Types changed: {type_changes}, Uppercase conversions: {case_changes}")

        # Save and close
        if not config["dry_run"]:
            save_options = SaveAsOptions()
            save_options.OverwriteExistingFile = True
            doc.SaveAs(file_path, save_options)
            log_message(f"  Saved successfully")
        else:
            log_message(f"  DRY RUN - not saved")

        doc.Close(False)
        return True

    except Exception as ex:
        log_message(f"  ERROR: {str(ex)}")
        return False


def run_batch_standardization(app, config=None):
    """Main entry point for batch processing."""

    if config is None:
        config = CONFIG

    log_file = config.get("log_file")
    library_path = config["library_path"]

    log_message("=" * 60, log_file)
    log_message("DETAIL LIBRARY TEXT STANDARDIZATION", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Library Path: {library_path}", log_file)
    log_message(f"Target Type: {config['text_type_name']}", log_file)
    log_message(f"Font: {config['font_name']}", log_file)
    log_message(f"Size: {config['text_size_inches']}\" (3/32\")", log_file)
    log_message(f"Dry Run: {config['dry_run']}", log_file)
    log_message("=" * 60, log_file)

    # Get all RVT files
    rvt_files = get_all_rvt_files(library_path)
    total_files = len(rvt_files)

    log_message(f"Found {total_files} RVT files to process", log_file)
    log_message("", log_file)

    success_count = 0
    fail_count = 0

    for i, file_path in enumerate(rvt_files):
        log_message(f"[{i+1}/{total_files}] ", log_file)

        if process_single_file(app, file_path, config):
            success_count += 1
        else:
            fail_count += 1

        log_message("", log_file)

    # Summary
    log_message("=" * 60, log_file)
    log_message("SUMMARY", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Total files: {total_files}", log_file)
    log_message(f"Successful: {success_count}", log_file)
    log_message(f"Failed: {fail_count}", log_file)
    log_message("=" * 60, log_file)

    return success_count, fail_count


# For running directly in pyRevit or RevitPythonShell
if __name__ == "__main__":
    try:
        # Get the Revit application
        # In pyRevit: __revit__ is available
        # In RevitPythonShell: use the provided app

        if '__revit__' in dir():
            app = __revit__.Application
        else:
            # Fallback for other environments
            from RevitServices.Persistence import DocumentManager
            app = DocumentManager.Instance.CurrentUIApplication.Application

        # Run the batch process
        run_batch_standardization(app, CONFIG)

    except Exception as ex:
        print(f"FATAL ERROR: {str(ex)}")

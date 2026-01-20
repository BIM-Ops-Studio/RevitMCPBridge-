@echo off
REM Auto Deploy RevitMCPBridge DLL
REM This script closes Revit, deploys the DLL, and reopens the project

cd /d D:\RevitMCPBridge2026\scripts
python revit_auto_deploy.py %*

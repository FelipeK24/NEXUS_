@echo off
cd /d "%~dp0"
if not exist "data\browser_profile" mkdir "data\browser_profile"
explorer "%~dp0data\browser_profile"

@echo off
rem ============================================================
rem  Complex n-th roots - interactive viewer
rem  Double-click this file to open the interactive window.
rem  Command line options are forwarded, e.g.
rem      run.bat -z "3+4i" -n 5
rem      run.bat -z "-8" -n 3 --print --no-gui
rem      run.bat -z "3+4i" -n 5 --save out.gif --no-gui
rem ============================================================
setlocal
cd /d "%~dp0"

rem --- 1. pick a Python 3 that already has tkinter + Pillow -------------
set "PY="
python -c "import tkinter, PIL" >nul 2>nul
if not errorlevel 1 set "PY=python"

if not defined PY (
  py -3 -c "import tkinter, PIL" >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)

rem --- 2. otherwise take any Python 3 with tkinter ---------------------
if not defined PY (
  python -c "import tkinter" >nul 2>nul
  if not errorlevel 1 set "PY=python"
)

if not defined PY (
  py -3 -c "import tkinter" >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)

if not defined PY (
  echo [!] Python 3 with tkinter was not found.
  echo     Install Python from https://www.python.org/downloads/ then run this file again.
  pause
  exit /b 1
)

rem --- 3. make sure Pillow is available --------------------------------
%PY% -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo [i] Installing required package: pillow ...
  %PY% -m pip install pillow
)

rem --- 4. run ----------------------------------------------------------
%PY% complex_roots.py %*
if errorlevel 1 (
  echo.
  echo [!] Failed to start. Check the message above.
  pause
)
endlocal

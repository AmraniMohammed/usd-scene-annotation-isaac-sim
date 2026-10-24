@echo off
rem Run a script with Isaac Sim's Python and the USD libraries it ships.
rem Isaac Sim's python.bat alone can't import pxr outside the app.
rem
rem Usage:
rem     set ISAAC_SIM=C:\path\to\isaac-sim-standalone-6.2.0-windows-x86_64
rem     isaac_python.bat annotate.py scene.usd config.json -o out\scene_annotated.usda

setlocal
if "%ISAAC_SIM%"=="" (
    echo Set ISAAC_SIM to the Isaac Sim install folder first.
    exit /b 1
)
for /d %%D in ("%ISAAC_SIM%\extscache\omni.usd.libs-*") do set "USD_LIBS=%%D"
for /d %%D in ("%ISAAC_SIM%\extscache\omni.usd.schema.semantics-*") do set "USD_SEM=%%D"
if "%USD_LIBS%"=="" (
    echo omni.usd.libs not found under %ISAAC_SIM%\extscache
    exit /b 1
)
set "PYTHONPATH=%USD_LIBS%;%USD_SEM%"
set "PATH=%USD_LIBS%\bin;%USD_SEM%\bin;%PATH%"
"%ISAAC_SIM%\kit\python\python.exe" %*

@echo off
pushd "%~dp0"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else if exist ".venv\bin\python.exe" (
  set "PY=.venv\bin\python.exe"
) else (
  echo Virtual environment not found. Run: python -m venv .venv
  pause
  popd
  exit /b 1
)

echo Starting Moto Track...
echo Press Ctrl+C to stop the server.
echo (LAN URLs are printed below when the server starts.)
echo.
"%PY%" app.py
if errorlevel 1 (
  echo.
  echo Server exited with an error. See messages above.
)
pause
popd

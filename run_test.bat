@echo off
pushd "%~dp0"
set MOTO_TRACK_TEST=1

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

echo Starting Moto Track in TEST mode at http://localhost:5000
echo Using database: tests\data\moto_track_test.db
echo Press Ctrl+C to stop the server.
echo.
"%PY%" app.py
pause
popd

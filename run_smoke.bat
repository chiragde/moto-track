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

"%PY%" tests\run_smoke.py
pause
popd

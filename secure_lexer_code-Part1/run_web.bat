@echo off
cd /d "%~dp0"
echo ============================================================
echo Starting Part 1: AI Secure Lexical Analyzer (FastAPI)
echo Web URL: http://localhost:8000
echo ============================================================
python -m uvicorn frontend.api:app --reload --port 8000
pause

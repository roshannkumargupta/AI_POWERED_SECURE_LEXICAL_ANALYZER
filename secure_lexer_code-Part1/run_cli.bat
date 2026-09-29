@echo off
cd /d "%~dp0"
echo ============================================================
echo Running Part 1: AI Secure Lexical Analyzer (CLI All Samples)
echo ============================================================
python -m ML_model.run_secure_engine --all-samples
pause

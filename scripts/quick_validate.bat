@echo off
chcp 65001 > nul
echo === Midscene Python Dependencies Quick Validation ===
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt file not found
    echo Please run: make requirements-freeze
    exit /b 1
)

echo 1. Checking requirements.txt file...
echo Success: requirements.txt exists

REM Count dependencies
for /f %%i in ('findstr /v "^#" requirements.txt ^| findstr /v "^$" ^| find /c "=="') do set count=%%i
echo Success: Found %count% dependency packages

echo.
echo 2. Validating key dependencies...

REM Check core dependencies
findstr /i "pydantic==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: pydantic) else (echo Error: pydantic & set error=1)

findstr /i "selenium==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: selenium) else (echo Error: selenium & set error=1)

findstr /i "playwright==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: playwright) else (echo Error: playwright & set error=1)

REM Check development dependencies
findstr /i "pytest==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: pytest) else (echo Error: pytest & set error=1)

findstr /i "black==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: black) else (echo Error: black & set error=1)

REM Check documentation dependencies
findstr /i "mkdocs==" requirements.txt >nul 2>&1
if %errorlevel% equ 0 (echo Success: mkdocs) else (echo Error: mkdocs & set error=1)

echo.
if defined error (
    echo Validation FAILED: Missing key dependencies
    exit /b 1
) else (
    echo Validation PASSED!
    echo requirements.txt contains all key dependencies
)
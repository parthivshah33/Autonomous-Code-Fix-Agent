@echo off
REM Docker run script for Multi-Agent Code Fixer (Windows)

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found. Creating from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo Please edit .env file and add your OPENAI_API_KEY
        exit /b 1
    ) else (
        echo Error: .env.example not found
        exit /b 1
    )
)

REM Default values
set TRACE_FILE=%1
if "%TRACE_FILE%"=="" set TRACE_FILE=data/input/trace_1.json

set TARGET_ROOT=%2
if "%TARGET_ROOT%"=="" set TARGET_ROOT=../fastapi-tdd-user-authentication

set OUTPUT_DIR=%3
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=data/output

echo Running Multi-Agent Code Fixer in Docker...
echo Trace file: %TRACE_FILE%
echo Target root: %TARGET_ROOT%
echo Output directory: %OUTPUT_DIR%
echo.

REM Build image if it doesn't exist
docker images | findstr "multi-agent-fixer" >nul
if errorlevel 1 (
    echo Building Docker image...
    docker build -t multi-agent-fixer:latest .
)

REM Run the container
docker run --rm ^
    -v "%CD%\data\input:/app/data/input:ro" ^
    -v "%CD%\data\output:/app/data/output" ^
    -v "%CD%\..\%TARGET_ROOT%:/app/target-codebase:ro" ^
    --env-file .env ^
    -e TARGET_ROOT_DIR=/app/target-codebase ^
    multi-agent-fixer:latest ^
    python main.py %TRACE_FILE% --target-root /app/target-codebase --output-dir %OUTPUT_DIR%

@echo off
REM Package script for shipping Multi-Agent Code Fixer (Windows)

set PACKAGE_NAME=multi-agent-fixer
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set VERSION=%datetime:~0,8%_%datetime:~8,6%
set OUTPUT_FILE=%PACKAGE_NAME%_%VERSION%.zip

echo Packaging Multi-Agent Code Fixer...
echo Output: %OUTPUT_FILE%
echo.

REM Create temporary directory
set TEMP_DIR=%TEMP%\multi-agent-fixer-package
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
set PACKAGE_DIR=%TEMP_DIR%\%PACKAGE_NAME%

REM Copy files
echo Copying files...
xcopy /E /I /Y src "%PACKAGE_DIR%\src"
xcopy /E /I /Y data "%PACKAGE_DIR%\data"
copy /Y main.py "%PACKAGE_DIR%\"
copy /Y requirements.txt "%PACKAGE_DIR%\"
copy /Y README.md "%PACKAGE_DIR%\"
copy /Y DOCKER.md "%PACKAGE_DIR%\"
copy /Y Dockerfile "%PACKAGE_DIR%\"
copy /Y docker-compose.yml "%PACKAGE_DIR%\"
copy /Y .dockerignore "%PACKAGE_DIR%\"
copy /Y .env.example "%PACKAGE_DIR%\"
copy /Y .gitignore "%PACKAGE_DIR%\"
copy /Y PROJECT_SUMMARY.md "%PACKAGE_DIR%\"
copy /Y run-docker.sh "%PACKAGE_DIR%\"
copy /Y run-docker.bat "%PACKAGE_DIR%\"
copy /Y package.bat "%PACKAGE_DIR%\"

REM Clean up unnecessary files
echo Cleaning up...
for /d /r "%PACKAGE_DIR%" %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q "%PACKAGE_DIR%\*.pyc" 2>nul
del /s /q "%PACKAGE_DIR%\*.pyo" 2>nul
del /s /q "%PACKAGE_DIR%\*.log" 2>nul

REM Note: Windows doesn't have zip by default, user needs 7-Zip or WinRAR
echo.
echo Package directory created at: %PACKAGE_DIR%
echo.
echo To create zip file, use 7-Zip or WinRAR:
echo   7z a -r %OUTPUT_FILE% "%PACKAGE_DIR%\*"
echo.
echo Or manually zip the contents of: %PACKAGE_DIR%
echo.
echo To ship:
echo   1. Send the zip file to the interviewer
echo   2. Include instructions to:
echo      - Extract the package
echo      - Copy .env.example to .env and add OPENAI_API_KEY
echo      - Run: docker build -t multi-agent-fixer:latest .
echo      - Run: run-docker.bat data\input\trace_1.json ..\target-codebase

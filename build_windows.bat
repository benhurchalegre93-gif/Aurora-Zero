@echo off
setlocal
cd /d "%~dp0"

echo Instalando dependencias...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo Gerando o executavel para Windows...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AuroraZero main.py
if errorlevel 1 goto :error

set "PACKAGE=dist\AuroraZero-Windows"
if exist "%PACKAGE%" rmdir /s /q "%PACKAGE%"
mkdir "%PACKAGE%\assets"
copy /y "dist\AuroraZero.exe" "%PACKAGE%\AuroraZero.exe" >nul
xcopy /e /i /y "assets" "%PACKAGE%\assets" >nul
copy /y "README.md" "%PACKAGE%\README.md" >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%PACKAGE%\*' -DestinationPath 'dist\AuroraZero-Windows.zip' -Force"
if errorlevel 1 goto :error

echo.
echo Entrega criada: %CD%\dist\AuroraZero-Windows.zip
pause
exit /b 0

:error
echo.
echo A compilacao falhou. Revise a mensagem acima e tente novamente.
pause
exit /b 1

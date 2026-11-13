@echo off
setlocal

set "ANKI_PROJECT_DIR=%~dp0"
start "Anki Isolated PowerShell" powershell.exe -NoExit -ExecutionPolicy Bypass -Command "$Host.UI.RawUI.WindowTitle = 'Anki Isolated'; Set-Location -LiteralPath $env:ANKI_PROJECT_DIR; $env:ANKI_BASE = Join-Path $env:ANKI_PROJECT_DIR 'Isolated-Data'; $env:ANKIDEV = '1'; $cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'; if (Test-Path (Join-Path $cargoBin 'cargo.exe')) { $env:PATH = $cargoBin + ';' + $env:PATH }; if (Test-Path 'C:\Program Files\Git\usr\bin\cp.exe') { $env:PATH = 'C:\Program Files\Git\usr\bin;' + $env:PATH }; if (Test-Path 'C:\msys64\usr\bin\rsync.exe') { $env:PATH = 'C:\msys64\usr\bin;' + $env:PATH }; & .\run.bat"

endlocal

:: launcher\launch.bat
@echo off
setlocal enabledelayedexpansion

REM ─── 1) Punto di partenza: cartella di questo .bat (sempre con backslash finale)
set "CURR=%~dp0"

REM Rimuove l’eventuale backslash finale
if "%CURR:~-1%"=="\" set "CURR=%CURR:~0,-1%"

:SEARCH_ROOT
  REM Se esistono .venv\Scripts\activate.bat e la cartella src, abbiamo trovato la root
  if exist "%CURR%\.venv\Scripts\activate.bat" if exist "%CURR%\src\" goto :FOUND

  REM Salva la cartella corrente e risali di uno
  set "LAST=%CURR%"
  pushd "%CURR%" >nul
    cd ..
    set "CURR=%CD%"
  popd   >nul

  REM Se non siamo saliti più su (raggiunta radice), esci con errore
  if "%CURR%"=="%LAST%" goto :NOT_FOUND

  goto :SEARCH_ROOT

:FOUND
  cd /d "%CURR%"
  call ".venv\Scripts\activate.bat"
  python -m src.ui.main_ui
  goto :EOF

:NOT_FOUND
  echo.
  echo ❌  Impossibile trovare la root del progetto.
  echo     Servono insieme: .venv\Scripts\activate.bat  e  src\ 
  echo     Controlla di aver creato il virtualenv nella cartella padre.
  pause
  exit /b 1

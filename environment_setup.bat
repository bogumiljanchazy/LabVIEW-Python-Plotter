@echo off
set VENV_DIR=.venv
set REQ_FILE=requirements.txt

:: 1. Sprawdzenie czy plik requirements istnieje
IF NOT EXIST "%REQ_FILE%" (
    echo [ERROR] Nie znaleziono pliku %REQ_FILE%!
    exit /b 1
)

:: 2. Sprawdzenie czy folder venv istnieje
IF NOT EXIST "%VENV_DIR%" (
    echo [INFO] Tworzenie srodowiska wirtualnego Python...
    :: Próba utworzenia venv. Zakładam, że python jest w zmiennych środowiskowych (PATH)
    python -m venv %VENV_DIR%
    
    IF ERRORLEVEL 1 (
        echo [ERROR] Nie udalo sie stworzyc venv. Sprawdz czy Python jest zainstalowany.
        exit /b 1
    )
) ELSE (
    echo [INFO] Srodowisko venv juz istnieje.
)

:: 3. Aktywacja i instalacja pakietow
:: W Windows aktywacja nie jest konieczna do instalacji, wystarczy użyć pip z wewnątrz venv
echo [INFO] Sprawdzanie i instalacja bibliotek...

"%VENV_DIR%\Scripts\python.exe" -m pip install -r %REQ_FILE%

IF ERRORLEVEL 1 (
    echo [ERROR] Blad podczas instalacji pakietow!
    exit /b 1
)

echo [SUCCESS] Srodowisko gotowe do pracy.
@echo off
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing requirements...
python -m pip install -r requirements.txt

echo.
echo Building application...
python build.py

echo.
echo Build process complete!
echo Press any key to exit...
pause >nul

deactivate

@echo off

rem Install the python virtual environment. 
rem python -m venv venv
rem Note: If multiple python versions are installed, use this command instead to use python 3.10
c:/python310/python.exe -m venv venv

rem Upgrade pip
call venv/Scripts/activate.bat
python.exe -m pip install --upgrade pip

rem Install requirements
python.exe -m pip install -r requirements.txt

pause
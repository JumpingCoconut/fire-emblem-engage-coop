@echo off
echo Starting python...
echo ----------------------------------------------------------------------------------
echo Remember to place your discord bot token in the config file ".env" !
echo ----------------------------------------------------------------------------------
echo .
echo .
dir static 
echo .
echo .
start /B cmd /C ".\venv\Scripts\activate.bat && python discord_fee_base.py"
pause
@echo off

REM Move to local_freight_tool folder
cd ..

call activate_environment
echo Running LGV forecast inputs
python scripts\lgv_forecast_inputs.py

cd scripts
pause

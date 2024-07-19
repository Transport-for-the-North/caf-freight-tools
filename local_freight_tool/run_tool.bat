@echo off

set env_name=freighttool
set python_script=LFT

call activate_conda
call conda activate %env_name%
python -m %python_script%
pause

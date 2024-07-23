@echo off

set env_name=freighttool

call activate_conda
call conda activate %env_name%
python -m LFT
pause

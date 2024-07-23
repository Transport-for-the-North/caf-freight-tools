@echo off

set env_name=freighttool

call activate_conda

echo Activating conda environment %env_name%
call conda activate %env_name%

@echo off

set env_name=freighttool
set env_file=environment.yml

call activate_conda
echo Creating %env_name%
call conda env list | find /i "%env_name%"
IF not errorlevel 1 (
    echo Found existing copy of %env_name%, removing
    call conda env remove -n %env_name%
)
call conda env create -f %env_file%
echo %env_name% created, you may exit this installer and use run_freight_tool.
echo If an error occurred, consult user guide Installation section.
pause

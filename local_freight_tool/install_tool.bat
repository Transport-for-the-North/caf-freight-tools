@echo off

set anaconda_path=%USERPROFILE%\Anaconda3
set miniconda_path=%USERPROFILE%\Miniconda3
set anaconda_activate=%anaconda_path%\Scripts\activate.bat
set miniconda_activate=%miniconda_path%\Scripts\activate.bat
set env_name=freighttool
set env_file=environment.yml


IF EXIST %anaconda_activate% (
    set env_path=%anaconda_path%\envs\%env_name%
    set activate=%anaconda_activate%
) ELSE (
    IF EXIST %miniconda_activate% (
        set env_path=%miniconda_path%\envs\%env_name%
        set activate=%miniconda_activate%
    ) ELSE (
        echo Please ensure Anaconda3 is installed to %USERPROFILE%\Anaconda3
        echo or Miniconda3 is installed to %USERPROFILE%\Miniconda3.
        echo Anaconda: https://www.anaconda.com/products/individual
        echo Miniconda: https://docs.conda.io/en/latest/miniconda.html
        echo If the filepath is different, please edit it in this script.
        pause
        exit
    )
)

call %activate%
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
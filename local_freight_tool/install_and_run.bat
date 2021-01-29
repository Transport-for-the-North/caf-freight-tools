@echo off

set anaconda_path=%USERPROFILE%\Anaconda3
set miniconda_path=%USERPROFILE%\Miniconda3
set anaconda_activate=%anaconda_path%\Scripts\activate.bat
set miniconda_activate=%miniconda_path%\Scripts\activate.bat
set env_name=freighttoolenv
set env_requirements=requirements.txt
set python_script=tc_main_menu.py


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

IF EXIST %env_path% (
    echo %env_name% environment exists
) ELSE (
    echo %env_name% environment doesn't exist.
    call %activate%
    echo Creating %env_name%
    call conda create -y --name %env_name% --file %env_requirements%
    pause
)

call %activate% %env_name%
python %python_script%
pause
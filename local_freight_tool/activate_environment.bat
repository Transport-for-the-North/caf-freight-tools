@echo off

set anaconda_path=%USERPROFILE%\Anaconda3
set miniconda_path=%USERPROFILE%\Miniconda3
set anaconda_activate=%anaconda_path%\Scripts\activate.bat
set miniconda_activate=%miniconda_path%\Scripts\activate.bat
set env_name=freighttool

IF EXIST %anaconda_activate% (
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

echo Activating conda environment %env_name%
call %activate% %env_name%

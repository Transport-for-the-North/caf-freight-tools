@echo off

set anaconda_path=%USERPROFILE%\Anaconda3
set miniconda_path=%USERPROFILE%\Miniconda3
set miniforge_path=%USERPROFILE%\miniforge3
set anaconda_activate=%anaconda_path%\Scripts\activate.bat
set miniconda_activate=%miniconda_path%\Scripts\activate.bat
set miniforge_activate=%miniforge_path%\Scripts\activate.bat

call where conda
IF NOT errorlevel 1 (
    echo Using conda from path
) ELSE IF EXIST %anaconda_activate% (
    echo Using %anaconda_activate%
    call %anaconda_activate%
) ELSE IF EXIST %miniconda_activate% (
    echo Using %miniconda_activate%
    call %miniconda_activate%
) ELSE IF EXIST %miniforge_activate% (
    echo Using %miniforge_activate%
    call %miniforge_activate%
) ELSE (
    echo Please ensure Anaconda3 is installed to %anaconda_path%,
    echo Miniconda3 is installed to %miniconda_path% or
    echo miniforge3 is installed to %miniforge_path%.
    echo Anaconda: https://www.anaconda.com/products/individual
    echo Miniconda: https://docs.conda.io/en/latest/miniconda.html
    echo If the filepath is different, please edit it in this script.
    pause
    exit
)

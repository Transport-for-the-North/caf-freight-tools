@echo off

echo Making pdf
call make latex
cd build\latex

REM Need to run this twice to get the contents page
call lualatex -interaction nonstopmode localfreighttool.tex
call lualatex -interaction nonstopmode localfreighttool.tex
cd ..\..

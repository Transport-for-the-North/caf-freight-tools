@echo off

set env_name=freighttool

call activate_conda
call conda activate %env_name%
echo Running LFT LGV Model
python -m LFT.lgv_model -c "lgv_model_config.yml"
pause

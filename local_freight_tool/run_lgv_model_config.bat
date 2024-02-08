@echo off

call activate_environment.bat
echo Running LFT LGV Model
python -m LFT.lgv_model -c "lgv_model_config.yml"
pause

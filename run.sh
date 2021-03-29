#!/bin/bash
CUDA_VISIBLE_DEVICES=$1 nohup gunicorn -w 1 --timeout 600 -b 0.0.0.0:$2 check_service:app > run_tqc.log 2>&1 &
# nohup python3 check_service.py > log_tqc.txt 2>&1 &
#nohup gunicorn -w 1 --timeout 600 -b 0.0.0.0:$1 check_service:app > run_tqc.log 2>&1 &
tail -f /dev/null

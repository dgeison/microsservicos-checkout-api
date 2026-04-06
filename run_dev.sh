# execute to permission: chmod +x run_dev.sh
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8085
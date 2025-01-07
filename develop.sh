virtualenv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip -e .
./docker-entrypoint.sh

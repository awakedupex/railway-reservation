#!/bin/bash
# Run this in your PythonAnywhere Bash console

git clone https://github.com/awakedupex/railway-reservation.git
cd railway-reservation

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn uvicorn

echo "DATABASE_URL=sqlite:///./sql_app.db" > .env
python seed.py

echo ""
echo "Setup complete!"
echo ""
echo "Next steps in the PythonAnywhere Web tab:"
echo "  1. WSGI file → replace with: from wsgi import app"
echo "  2. Virtualenv → /home/$(whoami)/railway-reservation/venv"
echo "  3. Reload"

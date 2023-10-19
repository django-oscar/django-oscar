docker compose up -d postgres

python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -e .\[test\]
pip install -r requirements.txt

export DATABASE_PORT=5432
export DATABASE_HOST=localhost
export DATABASE_PASSWORD=postgres
export DATABASE_USER=postgres

# Run Tests
pytest
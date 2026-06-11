dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:
	python run_seed.py

test:
	pytest tests/
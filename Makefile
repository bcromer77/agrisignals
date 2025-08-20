.PHONY: setup run-backend run-dashboard seed test format

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run-backend:
	. .venv/bin/activate && uvicorn backend.api.main:app --reload

run-dashboard:
	. .venv/bin/activate && streamlit run dashboard/app.py

seed:
	. .venv/bin/activate && python scripts/seed_mock.py

test:
	@echo "Add tests in ./tests and wire into CI"

format:
	@echo "Consider adding ruff/black for formatting and linting"

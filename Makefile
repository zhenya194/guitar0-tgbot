install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	python main.py

check:
	ruff check .
	ruff format --check .

fix:
	ruff check --fix .
	ruff format .

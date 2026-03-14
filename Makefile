# Install dependancies
install_dep:
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

# Create venv and install dependancies
create_and_install:
	python -m venv .venv
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

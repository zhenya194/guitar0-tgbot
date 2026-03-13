# Install dependancies
install_dep:
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

# Create venv and install dependancies
create_and_install_unix:
	python -m venv .venv
	source .venv/bin/activate
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

create_and_install_win_cmd:
	python -m venv .venv
	.venv\Scripts\activate
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

create_and_install_win_ps:
	python -m venv .venv
	.venv\Scripts\Activate.ps1
	pip install aiogram
	pip install pydantic-settings
	pip install python-dotenv
	pip install requests

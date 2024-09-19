hook:
	pre-commit install

setup:
	pip install -r requirements.txt

install: setup hook

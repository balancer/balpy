fmt: 
	poetry run isort .
	poetry run black .
	poetry run autopep8 . --recursive --in-place -a
	poetry run autoflake8 . --recursive --remove-unused-variables --in-place

lint: 
	poetry run flake8 . --max-line-length=150

test:
	poetry run pytest tests

all: fmt lint test
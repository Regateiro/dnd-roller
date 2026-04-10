.PHONY: lint

lint:
	poetry run black -l 150 **/*.py
	poetry run flake8 --max-line-length 150 **/*.py
	poetry run isort --profile black **/*.py
	poetry run pylint --errors-only --max-line-length 150 **/*.py

test:
	poetry run pytest --cov=bot
.PHONY: lint

lint:
	poetry run black -l 150 *.py utils/*.py
	poetry run flake8 --max-line-length 150 *.py utils/*.py
	poetry run isort --profile black *.py utils/*.py
	poetry run pylint --errors-only --max-line-length 150 *.py utils/*.py

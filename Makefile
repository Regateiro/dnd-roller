.PHONY: lint

lint:
	poetry run black -l 150 ./bot/**/*.py ./bot/*.py dnd_roller.py
	poetry run flake8 --max-line-length 150 ./bot/**/*.py ./bot/*.py dnd_roller.py
	poetry run isort --profile black ./bot/**/*.py ./bot/*.py dnd_roller.py
	poetry run pylint --errors-only --max-line-length 150 ./bot/**/*.py ./bot/*.py dnd_roller.py

test:
	poetry run pytest --cov=bot
.PHONY: lint

lint:
	black -l 150 dnd_roller.py utils/*.py
	flake8 --max-line-length 150 dnd_roller.py utils/*.py
	isort --profile black dnd_roller.py utils/*.py
	pylint --errors-only --max-line-length 150 dnd_roller.py utils/*.py

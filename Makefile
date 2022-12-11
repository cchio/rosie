init:
		pipenv install

test:
		pytest -q tests/test.py

.PHONY: init test
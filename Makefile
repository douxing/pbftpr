init:
	pip install -r requirements.txt

test:
	python -m unittest discover tests

.PHONY: init test

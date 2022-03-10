.PHONY: format lint test install bin clean

all: format lint test

format:
	black *.py awsdsc/*.py tests/*.py
	isort *.py awsdsc/*.py tests/*.py

lint:
	flake8 *.py awsdsc/*.py tests/*.py
	bandit -q *.py awsdsc/*.py
	mypy *.py awsdsc/*.py tests/*.py

test:
	python -m pytest ./tests

install:
	pip install .

bin:
	python pyinstaller.py

clean:
	rm -f awsdsc.spec
	rm -rf dist/

upload:
	python -m build --sdist
	python -m build --wheel
	twine check dist/*
	twine upload dist/*

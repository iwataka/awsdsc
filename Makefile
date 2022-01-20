.PHONY: format lint test install build clean

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

build:
	pyinstaller awsdsc/main.py \
		--onefile \
		--name awsdsc \
		--clean

clean:
	rm -f awsdsc.spec
	rm -rf dist/

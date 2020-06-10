.DEFAULT: help

help:
	@echo "Workspace Makefile"
	@echo "------------------"
	@echo
	@echo "make lint"
	@echo "    Runs linters"
	@echo
	@echo "make clean"
	@echo "    Removes compiled artefacts"
	@echo

lint:
	flake8

clean:
	npm run clean
	find . -name '__pycache__' -exec rm -rf {} +

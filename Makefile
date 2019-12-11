PACKAGES=home search workspace

.DEFAULT: help

help:
	@echo "Workspace Makefile"
	@echo "------------------"
	@echo
	@echo "make lint"
	@echo "    Runs pylint"

lint:
	pylint --rcfile=.pylintrc $(PACKAGES)

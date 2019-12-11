PACKAGES=home search workspace

.DEFAULT: help

help:
	@echo "Workspace Makefile"
	@echo "------------------"
	@echo
	@echo "make lint"
	@echo "    Runs pylint"
	@echo "make webpack"
	@echo "    Runs webpack to watch and compile assets"

webpack:
	./node_modules/.bin/webpack --config webpack.config.js --watch

lint:
	pylint --rcfile=.pylintrc $(PACKAGES)

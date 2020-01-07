.DEFAULT: help

help:
	@echo "Workspace Makefile"
	@echo "------------------"
	@echo
	@echo "make assets_clean"
	@echo "    Cleans up compiled assets folder"
	@echo "make assets_compile"
	@echo "    Runs webpack to compile assets"
	@echo "make assets_watch"
	@echo "    Runs webpack to watch and compile assets"
	@echo
	@echo "make lint"
	@echo "    Runs linters"
	@echo
	@echo "make clean"
	@echo "    Removes compiled artefacts"
	@echo

assets_clean:
	rm -f ./assets/webpack_bundles/*

assets_compile:
	./node_modules/.bin/webpack --config webpack.config.js

assets_watch:
	./node_modules/.bin/webpack --config webpack.config.js --watch

lint:
	flake8

clean:
	find . -name '__pycache__' -exec rm -rf {} +

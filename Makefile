.PHONY: htmllivereload

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  htmllivereload         runs Sphinx in livereload mode"

htmllivereload:
	@python sphinx_livereload.py
	@echo
	@echo "Live reload is running..."

.PHONY: all css

all:
	mkdocs build

css: docs/css/extra.css

docs/css/extra.css: docs/css/extra.scss docs/css/admonitions.scss
	sassc -t compact $< $@

docs/css/admonitions.scss: scripts/custom-admonitions.py
	python3 $<

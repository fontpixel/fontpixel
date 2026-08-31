PY := .venv/bin/python
PYTEST := .venv/bin/pytest

.PHONY: setup fonts dev build py-test ts-test e2e test

setup:
	python3 -m venv .venv && .venv/bin/pip -q install -e "pipeline[dev]"
	cd site && npm install

fonts:
	$(PY) -m opf.build --fonts fonts --out site/public/data --downloads dist-downloads --cache .cache
	$(PY) -m opf.brandfont --fonts fonts --data site/public/data --names site/src/i18n/sitenames.json
	mkdir -p site/public/downloads && rsync -a --delete dist-downloads/ site/public/downloads/

dev: fonts
	cd site && npm run dev

build: fonts
	cd site && npm run build

py-test:
	$(PYTEST) pipeline/tests -q

ts-test:
	cd site && npm test

e2e:
	cd site && npx playwright test

test: py-test ts-test

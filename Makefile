PY := .venv/bin/python
# Always go through `python -m`: the console scripts in .venv/bin carry an
# absolute shebang baked in at creation, so they break the moment the checkout
# is moved or renamed, while .venv/bin/python is a symlink and keeps working.
PYTEST := $(PY) -m pytest

.PHONY: setup fonts dev build py-test ts-test check e2e test

setup:
	python3 -m venv --clear .venv && $(PY) -m pip -q install -e "pipeline[dev]"
	cd site && bun install --frozen-lockfile

fonts:
	$(PY) -m opf.build --fonts fonts --out site/public/data --downloads dist-downloads --cache .cache
	$(PY) -m opf.brandfont --fonts fonts --data site/public/data --names site/src/i18n/sitenames.json
	mkdir -p site/public/downloads && rsync -a --delete dist-downloads/ site/public/downloads/

dev: fonts
	cd site && bun run dev

build: fonts
	cd site && bun run build

py-test:
	$(PYTEST) pipeline/tests -q

ts-test:
	cd site && bun run test

# astro check covers .astro/.ts; svelte-check covers the islands' templates,
# which astro check does not read. Without the second one a component can
# reference an i18n key that no longer exists and still build clean.
check:
	cd site && bun run check

e2e:
	cd site && bun run playwright test

test: py-test ts-test check

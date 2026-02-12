VENV_PYTHON:=.venv/bin/python
SRCS:=$(shell find src tests -name '*.py')

all: test

.venv: pyproject.toml
	uv sync

lint: .venv .lint
.lint: $(SRCS) $(TSCS)
	uv run flake8 $?
	touch $@

static: .venv .static
.static: $(SRCS) $(TSCS)
	echo "Code: $(SRCS)"
	echo "Test: $(TSCS)"
	uv run mypy $^
	touch $@

autopep8:
	uv run autopep8 --in-place $(SRCS)

unit: .venv
	uv run pytest

test: lint static unit

clean:
	rm -rf .lint .static
	rm -rf .mypy_cache
	-find src -type d -name __pycache__ -exec rm -fr "{}" \;

force-clean: clean
	rm -rf .venv

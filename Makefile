PEX_OUTPUT = dist/ariel.pex
PYTHON = venv/bin/python3

.PHONY: pex clean

pex: $(PEX_OUTPUT)

$(PEX_OUTPUT):
	mkdir -p dist
	$(PYTHON) -m pex . -e ariel:main -o $(PEX_OUTPUT) --python-shebang '/usr/bin/env python3' --include-tools

clean:
	rm -rf dist build *.egg-info

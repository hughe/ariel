PEX_OUTPUT = dist/ariel.pex
PYTHON = venv/bin/python3
STAGING = build/pex-sources

.PHONY: pex clean

pex: $(PEX_OUTPUT)

$(PEX_OUTPUT): ariel.py templates/index.html
	mkdir -p dist $(STAGING)/templates
	cp ariel.py $(STAGING)/
	cp templates/index.html $(STAGING)/templates/
	$(PYTHON) -m pex -r requirements.txt -D $(STAGING) -e ariel:main -o $(PEX_OUTPUT) --python-shebang '/usr/bin/env python3' --include-tools

install: pex
	cp ./dist/ariel.pex $(HOME)/bin/

clean:
	rm -rf dist build

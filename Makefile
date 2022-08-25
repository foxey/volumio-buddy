.DEFAULT_GOAL	:= all
CP				:= /bin/cp
echo			:= /bin/echo
GREP			:= grep
PYTHON			?= python3
SETUP			:= setup.py
SHELL			:= /bin/bash
SUDO			:= /usr/bin/sudo
SYSTEMCTL		:= /bin/systemctl

SERVICE			:= vbuddy
SERVICE_FILE	:= src/$(SERVICE).service
SYSTEMD_DIR		:= /etc/systemd/system

all: dev

.venv:
	$(PYTHON) -mvenv .venv
	@echo "Activate virtualenv with '. .venv/bin/activate'"

venv:
	@$(PYTHON) -c 'import sys; sys.exit(sys.prefix == sys.base_prefix)' || \
		(echo "Error: not in virtualenv "; exit 1)
	
lint: venv
	flake8 src
	flake8 tests

dev: venv
	$(PYTHON) -m pip install --upgrade pip setuptools wheel pytest pytest-aio
	$(PYTHON) -m pip install -r requirements.txt

test: venv
	$(PYTHON) -mpytest tests

build: venv test
	$(PYTHON) -m build

install: venv
	$(PYTHON) -m pip install -e .

service: install
	$(SUDO) $(CP) $(SERVICE_FILE) $(SYSTEMD_DIR)
	$(SUDO) $(SYSTEMCTL) daemon-reload
	$(SUDO) $(SYSTEMCTL) enable vbuddy

freeze:
	$(PYTHON) -m pip freeze | $(GREP) -v -e '^volumio-buddy-3==' -e '^pkg_resources==' > requirements.txt

clean:
	@rm -rf .pytest_cache/ build/ dist/
	@find . -not -path './.venv*' -path '*/__pycache__*' -delete
	@find . -not -path './.venv*' -path '*/*.egg-info*' -delete

clobber: clean
	@rm -rf .venv

.PHONY: lint dev test build install freeze clean clobber

.PHONY: fail-if-no-virtualenv all sandboxsetup super

all: fail-if-no-virtualenv super sandboxsetup

fail-if-no-virtualenv:
ifndef VIRTUAL_ENV # check for a virtualenv in development environment
ifndef PYENVPIPELINE_VIRTUALENV # check for jenkins pipeline virtualenv
$(error this makefile needs a virtualenv)
endif
endif

super:
	pip install -e ..

sandboxsetup: fail-if-no-virtualenv
	pip install .
	@make -C .. build_sandbox

%:
	@make -C .. $@
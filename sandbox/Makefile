.PHONY: fail-if-no-virtualenv all

all:
    @make -C .. install-python assets build_sandbox

fail-if-no-virtualenv:
ifndef VIRTUAL_ENV # check for a virtualenv in development environment
ifndef PYENVPIPELINE_VIRTUALENV # check for jenkins pipeline virtualenv
$(error this makefile needs a virtualenv)
endif
endif

%:
    @make -C .. $@
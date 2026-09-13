.PHONY: fail-if-no-virtualenv all sandboxsetup super

all: fail-if-no-virtualenv super build_sandbox

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

build_sandbox: fail-if-no-virtualenv sandboxsetup sandbox_clean sandbox_load_user sandbox_load_data ## Creates a sandbox from scratch

sandbox_clean: ## Clean sandbox images,cache,static and database
	# Remove media
	-rm -rf public/media/images
	-rm -rf public/media/cache
	-rm -rf public/static
	-rm -f db.sqlite
	# Create database
	manage.py migrate

sandbox_load_user: ## Load user data into sandbox
	manage.py loaddata fixtures/auth.json

sandbox_load_data: ## Import fixtures and collect static
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	manage.py loaddata fixtures/child_products.json
	manage.py oscar_import_catalogue fixtures/*.csv
	manage.py oscar_import_catalogue_images fixtures/images.tar.gz
	manage.py oscar_populate_countries --initial-only
	manage.py loaddata fixtures/pages.json fixtures/ranges.json fixtures/offers.json
	manage.py loaddata fixtures/orders.json
	manage.py clear_index --noinput
	manage.py update_index catalogue
	manage.py thumbnail cleanup
	manage.py collectstatic --noinput


%:
	@make -C .. $@
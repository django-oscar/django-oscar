VENV = venv
PYTEST = $(PWD)/$(VENV)/bin/py.test

# These targets are not files
.PHONY: install sandbox docs coverage lint messages compiledmessages css clean sandbox_image build-tools

install:
	pip install -r requirements.txt
	pip install -e .[test]

build_sandbox: sandbox_clean sandbox_load_user sandbox_load_data

sandbox_clean:
	# Remove media
	-rm -rf sandbox/public/media/images
	-rm -rf sandbox/public/media/cache
	-rm -rf sandbox/public/static
	-rm -f sandbox/db.sqlite
	# Create database
	sandbox/manage.py migrate

sandbox_load_user:
	sandbox/manage.py loaddata sandbox/fixtures/auth.json

sandbox_load_data:
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sandbox/manage.py loaddata sandbox/fixtures/child_products.json
	sandbox/manage.py oscar_import_catalogue sandbox/fixtures/*.csv
	sandbox/manage.py oscar_import_catalogue_images sandbox/fixtures/images.tar.gz
	sandbox/manage.py oscar_populate_countries --initial-only
	sandbox/manage.py loaddata sandbox/fixtures/pages.json sandbox/fixtures/ranges.json sandbox/fixtures/offers.json
	sandbox/manage.py loaddata sandbox/fixtures/orders.json sandbox/fixtures/promotions.json
	sandbox/manage.py clear_index --noinput
	sandbox/manage.py update_index catalogue
	sandbox/manage.py thumbnail cleanup
	sandbox/manage.py collectstatic --noinput

sandbox: install build_sandbox

sandbox_image:
	docker build -t django-oscar-sandbox:latest .

venv:
	virtualenv --python=$(shell which python3) $(VENV)
	$(VENV)/bin/pip install -e .[test]
	$(VENV)/bin/pip install -r docs/requirements.txt

docs: venv
	make -C docs html SPHINXBUILD=$(PWD)/$(VENV)/bin/sphinx-build

test: venv
	$(PYTEST)

retest: venv
	$(PYTEST) --lf

coverage: venv
	$(PYTEST) --cov=oscar --cov-report=term-missing

lint:
	flake8 src/oscar/
	flake8 tests/
	isort -q --recursive --diff src/
	isort -q --recursive --diff tests/

testmigrations:
	pip install -r requirements_migrations.txt
	cd sandbox && ./test_migrations.sh

messages:
	# Create the .po files used for i18n
	cd src/oscar; django-admin.py makemessages -a

compiledmessages:
	# Compile the gettext files
	cd src/oscar; django-admin.py compilemessages

css:
	npm install
	npm run build

clean:
	# Remove files not in source control
	find . -type f -name "*.pyc" -delete
	rm -rf nosetests.xml coverage.xml htmlcov *.egg-info *.pdf dist violations.txt
	rm -rf dist

todo:
	# Look for areas of the code that need updating when some event has taken place (like
	# Oscar dropping support for a Django version)
	-grep -rnH TODO *.txt
	-grep -rnH TODO src/oscar/apps/
	-grep -rnH "django.VERSION" src/oscar/apps

build-tools:
	pip install twine wheel

dist: build-tools clean
	python setup.py sdist bdist_wheel
	$(MAKE) -w -C metapackage dist

release: dist
	twine upload -s dist/*
	$(MAKE) -C metapackage release

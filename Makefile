# These targets are not files
.PHONY: install sandbox docs coverage lint messages compiledmessages css clean sandbox_image

install:
	pip install -r requirements.txt
	pip install -e .[test]

build_sandbox:
	# Remove media
	-rm -rf sites/sandbox/public/media/images
	-rm -rf sites/sandbox/public/media/cache
	-rm -rf sites/sandbox/public/static
	-rm -f sites/sandbox/db.sqlite
	# Create database
	sites/sandbox/manage.py migrate
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/child_products.json
	sites/sandbox/manage.py oscar_import_catalogue sites/sandbox/fixtures/*.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/sandbox/fixtures/images.tar.gz
	sites/sandbox/manage.py oscar_populate_countries --initial-only
	sites/sandbox/manage.py loaddata sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json sites/_fixtures/offers.json
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/orders.json
	sites/sandbox/manage.py clear_index --noinput
	sites/sandbox/manage.py update_index catalogue
	sites/sandbox/manage.py thumbnail cleanup

sandbox: install build_sandbox

sandbox_image:
	docker build -t django-oscar-sandbox:latest .

docs:
	cd docs && make html

test:
	py.test 

coverage:
	py.test --cov=oscar --cov-report=term-missing

lint:
	flake8 src/oscar/
	isort -q --recursive --diff src/

testmigrations:
	pip install -r requirements_migrations.txt
	cd sites/sandbox && ./test_migrations.sh

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

todo:
	# Look for areas of the code that need updating when some event has taken place (like 
	# Oscar dropping support for a Django version)
	-grep -rnH TODO *.txt
	-grep -rnH TODO src/oscar/apps/
	-grep -rnH "django.VERSION" src/oscar/apps


release: clean
	pip install twine wheel
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload -s dist/*

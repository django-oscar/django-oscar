# These targets are not files
.PHONY: install sandbox docs coverage lint messages compiledmessages css clean sandbox_image

install:
	pip install -r requirements.txt
	pip install -e .[test]

build_sandbox:
	# Remove media
	-rm -rf sandbox/public/media/images
	-rm -rf sandbox/public/media/cache
	-rm -rf sandbox/public/static
	-rm -f sandbox/db.sqlite
	# Create database
	sandbox/manage.py migrate
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sandbox/manage.py loaddata sandbox/fixtures/child_products.json
	sandbox/manage.py oscar_import_catalogue sandbox/fixtures/*.csv
	sandbox/manage.py oscar_import_catalogue_images sandbox/fixtures/images.tar.gz
	sandbox/manage.py oscar_populate_countries --initial-only
	sandbox/manage.py loaddata sandbox/fixtures/pages.json sandbox/fixtures/auth.json sandbox/fixtures/ranges.json sandbox/fixtures/offers.json
	sandbox/manage.py loaddata sandbox/fixtures/orders.json sandbox/fixtures/promotions.json
	sandbox/manage.py clear_index --noinput
	sandbox/manage.py update_index catalogue
	sandbox/manage.py thumbnail cleanup
	sandbox/manage.py collectstatic --noinput

sandbox: install build_sandbox

sandbox_image:
	docker build -t django-oscar-sandbox:latest .

docs:
	cd docs && make html

test:
	py.test 

retest:
	py.test --lf 

coverage:
	py.test --cov=oscar --cov-report=term-missing

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

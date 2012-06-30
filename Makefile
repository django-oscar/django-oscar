sandbox:
	# Create a sandbox installation for playing around with oscar.
	mkvirtualenv oscar
	python setup.up develop
	pip install -r requirements.txt
	# Create database
	sandbox/manage.py syncdb --noinput
	sandbox/manage.py migrate
	# Import some fixtures
	sandbox/manage.py oscar_import_catalogue sandbox/data/books-catalogue.csv
	sandbox/manage.py oscar_import_catalogue_images sandbox/data/books-images.tar.gz
	sandbox/manage.py loaddata countries.json sandbox/fixtures/pages.json

test:
	./runtests.py
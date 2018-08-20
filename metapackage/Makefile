.PHONY: clean

all: dist

clean:
	rm -rf dist build django_oscar.egg-info

dist: clean
	python metasetup.py sdist bdist_wheel

release: dist
	twine upload -s dist/*

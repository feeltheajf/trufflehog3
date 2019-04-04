.PHONY: test push
.ONESHELL:

test: unittest build disttest

unittest:
	pytest --cov=./truffleHog3 && codecov

build: clean
	python3 setup.py sdist bdist_wheel

disttest:
	twine check dist/*

push:
	twine upload dist/* -u feeltheajf

clean:
	rm -rf build dist *.egg-info

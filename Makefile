.PHONY: test build push clean
.ONESHELL:

test: clean
	pytest --cov=./truffleHog3 --cov-report=term-missing && codecov

build: clean
	python3 setup.py sdist bdist_wheel
	twine check dist/*

push: build
	twine upload dist/* -u feeltheajf

clean:
	rm -rf build dist *.egg-info .coverage* *coverage* .*cache

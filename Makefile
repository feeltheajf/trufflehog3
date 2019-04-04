.PHONY: test push clean
.ONESHELL:

test:
	pytest --cov=./truffleHog3 && codecov

push: clean
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	twine upload dist/* -u feeltheajf

clean:
	rm -rf build dist *.egg-info

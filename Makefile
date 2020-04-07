.PHONY: test unittest build-docker test-docker build push clean
.ONESHELL:

test: unittest clean build-docker test-docker

unittest:
	PYTHONPATH="." pytest -vv --cov=./truffleHog3 --cov-report=term-missing && codecov

build-docker:
	docker build -t trufflehog3 .

test-docker:
	docker run \
		-it \
		--rm \
		--volume ${CURDIR}:/source \
		--volume ${CURDIR}/scripts/maketest:/maketest \
		--entrypoint /maketest \
		trufflehog3

build: clean
	python3 setup.py sdist bdist_wheel
	twine check dist/*

push: build
	twine upload dist/* -u feeltheajf

clean:
	rm -rf build dist *.egg-info .coverage* *coverage* .*cache

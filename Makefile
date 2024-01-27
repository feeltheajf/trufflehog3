.ONESHELL:

APP = trufflehog3
IMG = $(APP)-dev
TMP = /tmp/$(APP)

.PHONY: test
test: unittest codecov clean build-docker test-docker

.PHONY: unittest
unittest:
	PYTHONPATH="." pytest -vvv

.PHONY: codecov
codecov:
	codecov

.PHONY: docs
docs:
	pdoc --html --template-dir docs/templates -o $(TMP) -f trufflehog3 \
		&& rm docs/*.html \
		&& mv $(TMP)/$(APP)/*.html ./docs

.PHONY: build-docker
build-docker:
	docker build -f Dockerfile.dev -t $(IMG) .

.PHONY: test-docker
test-docker: build-docker
	docker run \
		--rm \
		--volume ${CURDIR}:/source:ro \
		--volume ${CURDIR}/scripts/maketest:/maketest:ro \
		--entrypoint /maketest \
		$(IMG)

.PHONY: build
build: clean
	python3 setup.py sdist bdist_wheel
	twine check dist/*

.PHONY: push
push: push-pypi

.PHONY: push-pypi
push-pypi: build
	twine upload dist/* -u __token__

.PHONY: clean
clean:
	rm -rf build dist *.egg-info .coverage* *coverage* .*cache

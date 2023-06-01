PACKAGE_NAME?="pquisby"
PUSH_TO?="pypi"

.PHONY: build build-push local localdev clean
	
build:
	python setup.py sdist bdist_wheel

build-push:
	$(MAKE) clean
	./package_version.sh ${PUSH_TO} ${PACKAGE_NAME}
	$(MAKE) build
	twine upload --verbose --repository ${PUSH_TO} dist/*

local:
	$(MAKE) clean
	./package_version.sh ${PUSH_TO} ${PACKAGE_NAME}
	pip install .

localdev:
	$(MAKE) clean
	./package_version.sh ${PUSH_TO} ${PACKAGE_NAME}
	pip install -e .

clean:
	rm -rf setup.py build dist
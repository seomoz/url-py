.PHONY: test
test: url/url.so
	# TODO(dan): coverage with Cython
	nosetests --verbose

url/url.so: url/url.cpp url/url.pyx url/url.pxd url/url-cpp/src/*.cpp url/url-cpp/include/*.h
	python setup.py build_ext --inplace

install:
	python setup.py install

requirements:
	pip freeze | grep -v url > requirements.txt

clean:
	rm -rf url.egg-info build dist
	find . -name '*.pyc' | xargs --no-run-if-empty rm -f
	find url -name '*.so' | xargs --no-run-if-empty rm -f

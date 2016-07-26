.PHONY: test
test:
	nosetests --with-coverage

install:
	python setup.py install

requirements:
	pip freeze | grep -v url > requirements.txt

clean:
	rm -rf url.egg-info build dist
	find . -name '*.pyc' | xargs --no-run-if-empty rm -f

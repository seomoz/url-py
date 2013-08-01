clean:
	# Remove the build
	rm -rf url.egg-info build dist
	# And all of our pyc files
	find . -name '*.pyc' | xargs -n 100 rm
	# And lastly, .coverage files
	find . -name .coverage | xargs rm

nose:
	rm -f .coverage
	nosetests --exe --cover-package=url --with-coverage --cover-branches -v

test: nose

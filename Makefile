wheel:
	python setup.py bdist_wheel

docs:
	pdoc --html --force --output-dir docs -c sort_identifiers=False shimmer_listener
	mv docs/shimmer_listener/* docs/
	rm -rf docs/shimmer_listener

clean :
	rm -rf build dist shimmer_listener.egg-info

clean-docs:
	rm -rf docs

.PHONY : wheel
.PHONY : clean
.PHONY : clean-docs
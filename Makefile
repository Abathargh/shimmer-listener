test :
	python -m unittest discover tests

wheel :
	python setup.py bdist_wheel

build :
	python -m pip install --upgrade build && python -m build

upload :
	twine upload --repository pypi dist/*

docs :
	pdoc --html --force --output-dir docs -c sort_identifiers=False shimmer_listener
	mv docs/shimmer_listener/* docs/
	rm -rf docs/shimmer_listener

clean :
	rm -rf build dist shimmer_listener.egg-info

clean-docs:
	rm -rf docs

.PHONY : test
.PHONY : wheel
.PHONY : build
.PHONY : upload
.PHONY : clean
.PHONY : clean-docs
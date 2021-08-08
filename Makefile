ifdef OS
	RM = rd /S /Q 
	MV = move
else
	RM = rm -rf
	MV = mv
endif

wheel :
	python3 setup.py bdist_wheel

docs:
	pdoc --html --force --output-dir docs -c sort_identifiers=False shimmer_listener
	$(MV) docs/shimmer_listener/* docs/
	$(RM) docs/shimmer_listener

clean :
	$(RM) build dist shimmer_listener.egg-info

clean-docs:
	$(RM) docs

.PHONY : wheel
.PHONY : clean
.PHONY : clean-docs
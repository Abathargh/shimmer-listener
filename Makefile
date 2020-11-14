wheel :
	python3 setup.py bdist_wheel

clean :
	rm -rf build dist shimmer_listener.egg-info

.PHONY : clean
.PHONY : wheel
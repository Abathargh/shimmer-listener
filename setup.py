from setuptools import setup, find_packages

with open("README.md", "r") as f:
    desc = f.read()

setup(
    name="shimmer-listener",
    version="0.1",
    description="shimmer2 data listener, based on the work contained in "
                "https://github.com/ShimmerResearch/tinyos-shimmer",
    long_description=desc,
    long_description_content_type="text/markdown",
    author="Gianmarco Marcello",
    author_email='g.marcello@antima.it',
    python_requires=">=3.5",
    install_requires=["pybluez"],
    license="MPL2.0",
    data_files=[("", ["LICENSE"])],
    packages=find_packages(),
    scripts=["scripts/shimmer-to-nodered"]
)

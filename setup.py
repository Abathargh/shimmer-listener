from setuptools import setup, find_packages


with open("README.md", "r") as f:
    desc = f.read()


setup(
    name="shimmer-listener",
    version="0.3",
    description="shimmer2 data listener, based on the work contained in "
                "https://github.com/ShimmerResearch/tinyos-shimmer",
    long_description=desc,
    long_description_content_type="text/markdown",
    author="Gianmarco Marcello",
    author_email='g.marcello@antima.it',
    python_requires=">=3.6",
    install_requires=["pybluez"],
    license="MPL2.0",
    data_files=[("", ["LICENSE"])],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "shimmer-to-nodered=shimmer_listener._console_scripts:nodered_app",
            "shimmer-printer=shimmer_listener._console_scripts:printer_app",
            "shimmer-btslave=shimmer_listener._console_scripts:btmastertest_app"
        ]
    }
)

from setuptools import setup, find_packages


with open("README.md", "r") as f:
    desc = f.read()


setup(
    name="shimmer-listener",
    version="0.3.1",
    description="A library to process bluetooth data from a shimmer2 runnning tinyos",
    long_description=desc,
    long_description_content_type="text/markdown",
    author="Gianmarco Marcello",
    author_email='g.marcello@antima.it',
    python_requires=">=3.6",
    install_requires=["pybluez"],
    license="GPLv2.0",
    data_files=[("", ["LICENSE"])],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "shimmer-printer=shimmer_listener.console_scripts:printer_app",
            "shimmer-btslave=shimmer_listener.console_scripts:btmastertest_app"
        ]
    }
)

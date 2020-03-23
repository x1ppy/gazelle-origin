import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="red-origin",
    version="1.0.0",
    author="x1ppy",
    author_email="",
    packages=[''],
    scripts=['red-origin'],
    description="RED origin.txt generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/x1ppy/red-origin",
    python_requires='>=3.6',
    install_requires=[
        "requests",
    ],
)

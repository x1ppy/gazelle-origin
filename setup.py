import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gazelle-origin",
    version="2.0.2",
    author="x1ppy",
    author_email="",
    packages=[''],
    scripts=['gazelle-origin'],
    description="Gazelle origin.yaml generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/x1ppy/gazelle-origin",
    python_requires='>=3.6',
    install_requires=[
        "pyyaml",
        "requests",
    ],
)

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='slipstream',
    version='0.0.1',
    author='Belicito',
    author_email='belicito@github.com',
    description='Slipstream',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/belicito/slipstream.git'
    project_urls = {
        "Bug Tracker": "https://github.com/belicito/slipstream/issues"
    },
    license='MIT',
    packages=['slipstream', 'slipstream.data', 'slipstream.sim'],
    install_requires=['numpy', 'pandas', 'pytz'],
)

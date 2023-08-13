import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='slipstream',
    version='0.0.3',
    author='Belicito',
    author_email='belicito@github.com',
    description='Slipstream',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/belicito/slipstream.git",
    project_urls = {
        "Bug Tracker": "https://github.com/belicito/slipstream/issues"
    },
    license='MIT',
    packages=[
        'slipstream', 
        'slipstream.data', 
        'slipstream.trading', 
        'slipstream.fsm', 
        'slipstream.market'
    ],
    entry_points = {
        "console_scripts": [
            "slipstream = slipstream.cli:main"
        ]
    },
    install_requires=['numpy', 'pandas', 'pytz', 'pydispatcher'],
)

from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    readme = f.read()

setup(
    name='beets-wanted-albums',
    version='0.1.0',
    description='Plugin for the music library manager Beets. Discover new or old albums missing from your music collection, and take action!',
    long_description=readme,
    url='https://github.com/gryphonmyers/beets-wanted-albums-plugin',
    download_url='https://github.com/gryphonmyers/beets-wanted-albums-plugin.git',
    author='Gryphon Myers',
    author_email='gryphon@gryphonmyers.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='beets',
    packages=['beetsplug'],
    install_requires=['beets>=1.6.0'],
)
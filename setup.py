#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='gitanal',
      version='0.0.8',
      description='Tool to analyze git repositories',
      author='Marek Wiewiorski',
      author_email='mwicat@gmail.com',
      include_package_data=True,
      zip_safe=False,
      packages=find_packages(),
      package_dir={'gitanal': 'gitanal'},
      install_requires=[
        'argh>=0.24.1',
        'argcomplete',
        'GitPython',
        'Jinja',
        'python-dateutil',
        'python-datemath'
      ],
      entry_points={'console_scripts': [
          'gitanal = gitanal.main:main']
      }
)

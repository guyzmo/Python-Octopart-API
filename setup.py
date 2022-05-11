from setuptools import setup
import os
import sys

if sys.version_info.major != 3:
    raise Exception("Sorry this package only works with python3.")

setup(name='pyoctopart',
      version='0.6.3',
      description="Python library to connect to Octopart",
      long_description_markdown_filename='README.md',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved',
          'Operating System :: Unix',
      ],
      keywords='download tv show',
      author='Bernard `Guyzmo` Pratz',
      author_email='pyoctopart@m0g.net',
      url='https://github.com/guyzmo/pyoctopart',
      license='GPLv3',
      packages=['pyoctopart'],
      zip_safe=False,
      setup_requires=[
          'setuptools-markdown',
          'pypandoc<=1.7.5'
        ],
      install_requires=[
          'pypandoc<=1.7.5'
          'pyoctopart',
          'requests',
          'setuptools'
      ],
      )

if "install" in sys.argv:
    print("""
Python Octopart API Library is now installed!

To start using it, call:

    python3
    >>> from pyoctopart.octopart import Octopart
    >>> help(Octopart)

""")

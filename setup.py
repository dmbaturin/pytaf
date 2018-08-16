from setuptools import setup


setup(name='pytaf',
      version='1.2.1',
      description='TAF (Terminal Aerodrome Forecast) and METAR parser and decoder',
      url='http://github.com/dmbaturin/pytaf',
      author='Daniil Baturin',
      author_email='daniil@baturin.org',
      license='MIT',
      package_dir={'': 'lib'},
      packages=['pytaf'],
      zip_safe=True,
      classifiers = [
                        "Development Status :: 5 - Production/Stable",
                        "License :: OSI Approved :: MIT License",
                        "Operating System :: OS Independent",
                        "Programming Language :: Python :: 2.6",
                        "Programming Language :: Python :: 2.7",
                        "Programming Language :: Python :: 3",
                        "Topic :: Scientific/Engineering"
                    ],
      keywords="aviation weather meteorology taf metar"
)


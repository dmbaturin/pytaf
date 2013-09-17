from setuptools import setup


setup(name='pytaf',
      version='0.1.3',
      description='TAF (Terminal Aerodrome Forecast) parser and decoder',
      url='http://github.com/dmbaturin/pytaf',
      author='Daniil Baturin',
      author_email='daniil@baturin.org',
      license='MIT',
      package_dir={'': 'lib'},
      packages=['pytaf'],
      zip_safe=True,
      classifiers = [
                        "Development Status :: 3 - Alpha",
                        "License :: OSI Approved :: MIT License",
                        "Operating System :: OS Independent",
                    ]
)


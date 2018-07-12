import os
import pathlib

from setuptools import setup, find_packages

setup_path = pathlib.Path(os.path.dirname(os.path.relpath(__file__)))
readme_path = setup_path.joinpath('README.md').as_posix()
with open(readme_path, encoding='utf-8', mode='r') as f:
    long_description = f.read()

setup(name='AudioConverter',
      use_scm_version={'root': '.', 'relative_to': __file__},
      setup_requires=['setuptools_scm']
      desciption='Audio Converter CLI',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='lamdav',
      author_email='david.lam@lamdav.com',
      license='MIT',
      python_requires='>=3.5',
      entry_points={
        'console_scripts': [
            'audioconvert=AudioConverter.converter:cli'
        ]
      },
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Utilities'
      ],
      install_requires=[
        'click==6.7',
        'colorama==0.3.9',
        'pydub==0.22.1'
      ],
      keywords=['audioconverter audio converter CLI']
      include_package_data=True
)

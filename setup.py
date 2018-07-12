from setuptools import setup

setup(name='AudioConverter',
      desciption='Audio Converter CLI',
      author='lamdav',
      author_email='david.lam@lamdav.com',
      license='MIT',
      python_requires='>=3.5',
      entry_points={
        'console_scripts': [
            'audioconvert=AudioConverter.converter:cli'
        ]
      },
      include_package_data=True
)

from setuptools import setup, find_packages

setup(
    name='sort',
    version='1.0.0',
    description='A simple online and realtime tracking algorithm',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/FarahAbdo/sort',  # Replace with your GitHub username
    author='Farah Abdou',  # Replace with your name
    author_email='faraahabdou@gmail.com',  # Replace with your email
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'filterpy'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

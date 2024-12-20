from setuptools import setup, find_packages

setup(
    name="movie_opt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "argparse",
    ],
    entry_points={
        "console_scripts": [
            "movie_opt=movie_opt.main:main",
        ],
    },
)
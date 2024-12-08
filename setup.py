from setuptools import setup, find_packages

setup(
    name="image-quality-sorter",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'openai>=1.0.0',
        'Pillow>=10.0.0',
        'PyYAML>=6.0',
        'python-dotenv>=1.0.0',
    ],
) 
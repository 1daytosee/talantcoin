from setuptools import setup, find_packages

setup(
    name="talantchain",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "pynacl",
        "fastapi",
        "pydantic",
        "uvicorn",
        "aiohttp",
        "base58"
    ],
    entry_points={
        'console_scripts': [
            'talantchain=talantchain.cli:main',
        ],
    },
    python_requires='>=3.8',
    author="TalantChain Team",
    description="Python implementation of TalantChain cryptocurrency",
    keywords="blockchain, cryptocurrency, talantchain",
)

from setuptools import setup, find_packages

setup(
    name="minert1",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "cryptography>=3.4.0",
        "requests>=2.26.0",
        "psutil>=5.8.0"
    ],
    entry_points={
        "console_scripts": [
            "minert1=minert1.miner:main",
        ],
    },
    author="TalantChain Team",
    description="CPU-optimized cryptocurrency miner for TalantChain",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="cryptocurrency, mining, cpu-mining, talantchain",
    url="https://github.com/yourusername/minert1",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)

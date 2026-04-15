from setuptools import setup, find_packages

setup(
    name="godelOS",
    version="0.2.0-beta",
    description="A comprehensive symbolic cognition engine",
    author="GödelOS Team",
    author_email="info@godelOS.org",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
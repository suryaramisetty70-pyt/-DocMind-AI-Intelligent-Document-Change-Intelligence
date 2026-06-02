"""
DocMind AI - Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="docmind-ai",
    version="1.0.0",
    author="DocMind AI Team",
    author_email="support@docmind.ai",
    description="Intelligent Document Change Intelligence Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/docmind-ai/docmind-ai",
    project_urls={
        "Bug Tracker": "https://github.com/docmind-ai/docmind-ai/issues",
        "Documentation": "https://docs.docmind.ai",
        "Source Code": "https://github.com/docmind-ai/docmind-ai"
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "ui"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Enterprise",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
        "Topic :: Information Analysis"
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0"
        ],
        "gpu": [
            "torch>=2.0.0",
            "easyocr>=1.7.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "docmind=docmind_ai.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "document",
        "intelligence",
        "comparison",
        "diff",
        "ocr",
        "ai",
        "nlp",
        "semantic",
        "fraud",
        "risk",
        "compliance",
        "contract",
        "legal"
    ],
    project_urls={
        "Documentation": "https://docs.docmind.ai",
    }
)
"""
DocMind AI - Setup Configuration
"""

from setuptools import setup, find_packages

setup(
    name="docmind-ai",
    version="3.0",
    description="DocMind AI - Intelligent Document Change Intelligence Platform",
    author="DocMind AI Team",
    author_email="team@docmind.ai",
    url="https://github.com/suryaramisetty70-pyt/-DocMind-AI-Intelligent-Document-Change-Intelligence",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pdfplumber>=0.10.0",
        "openpyxl>=3.1.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "sentence-transformers>=2.2.0",
        "plotly>=5.15.0",
        "python-docx>=1.0.0",
        "python-multipart>=0.0.6",
        "reportlab>=4.0.0",
        "pillow>=10.0.0",
    ],
    extras_require={
        "ocr": ["easyocr", "pytesseract", "opencv-python"],
        "full": ["langchain", "faiss-cpu"],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

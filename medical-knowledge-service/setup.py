"""
Medical Knowledge Service Setup
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="medical-knowledge-service",
    version="1.0.0",
    description="医学知识库向量检索服务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lingxi Health",
    url="https://github.com/your-org/home-health",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Medical Science.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "asyncpg>=0.29.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ]
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "medical-knowledge-api=medical_knowledge_service.api:main",
        ],
    },
)

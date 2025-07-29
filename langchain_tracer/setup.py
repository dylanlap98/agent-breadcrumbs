"""
Setup script for langchain_tracer package
"""

from setuptools import setup, find_packages

# Read the README file
with open("langchain_tracer/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="langchain-tracer",
    version="0.1.0",
    author="Agent Breadcrumbs Team",
    author_email="your-email@example.com",
    description="HTTP-level tracing for complete LLM observability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agent-breadcrumbs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "requests>=2.25.0",
        # Optional dependencies for better functionality
    ],
    extras_require={
        "all": [
            "httpx>=0.24.0",
            "aiohttp>=3.8.0",
            "flask>=2.0.0",
            "flask-cors>=4.0.0",
        ],
        "dashboard": [
            "flask>=2.0.0",
            "flask-cors>=4.0.0",
        ],
        "async": [
            "httpx>=0.24.0",
            "aiohttp>=3.8.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "langchain-tracer=langchain_tracer.cli:main",
        ],
    },
    package_data={
        "langchain_tracer": [
            "dashboard/templates/*.html",
            "dashboard/static/*",
        ],
    },
    include_package_data=True,
    keywords="llm, observability, tracing, langchain, openai, monitoring",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/agent-breadcrumbs/issues",
        "Source": "https://github.com/yourusername/agent-breadcrumbs",
        "Documentation": "https://github.com/yourusername/agent-breadcrumbs/blob/main/README.md",
    },
)

from setuptools import setup, find_packages

setup(
    name="pyMifare",
    version="1.0.0",
    author="Spark Drago",
    author_email="your_email@example.com",
    description="Python library for interfacing with MIFARE RFID card readers using pyMifare protocol",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyMifare",
    packages=find_packages(),
    install_requires=[
        "pyserial",
    ],
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="folder-syncer",
    version="1.0.0",
    author="Folder Syncer Contributors",
    author_email="your.email@example.com",
    description="A GUI application for synchronizing folders with real-time monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/folder-syncer",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Filesystems",
        "Topic :: Desktop Environment :: File Managers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: GTK",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.6",
    install_requires=[
        "watchdog>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "folder-syncer=main:main",
        ],
        "gui_scripts": [
            "folder-syncer-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["LICENSE", "README.md"],
    },
)

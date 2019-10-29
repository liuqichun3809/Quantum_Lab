import platform
from codecs import open
from os import getcwd, getenv, listdir, path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# This reads the __version__ variable from lab/_version.py
exec(open('qulab/_version.py').read())

requirements = [
    'attrs>=17.4.0',
    'aiohttp>=3.2.1',
    'numpy>=1.13.3',
    'scipy>=1.0.0',
    'matplotlib>=2.1.0',
    'jupyter>=1.0.0',
    'requests>=2.18.4',
    'tornado>=5.0.1',
    'motor>=1.2.1',
    'mongoengine>=0.15.0',
    'blinker>=1.4',
    'pyvisa>=1.8',
    'pyvisa-py>=0.2',
    'PyYAML>=3.12',
    'quantities>=0.12.1',
    'ruamel.yaml>=0.16.5',
]

if platform.system() == 'Windows':
    requirements.extend([
        'pywin32>=220.1'
    ])

setup(
    name="Quantum_Lab",
    version=__version__,
    author="LQC",
    author_email="liuqichun3809@163.com",
    url="https://github.com/liuqichun3809/Quantum_Lab",
    license = "MIT",
    keywords="experiment laboratory",
    description="contral instruments and manage data",
    long_description=long_description,
    packages = find_packages(),
    include_package_data = True,
    install_requires=requirements,
    extras_require={
        'test': ['pytest'],
    },
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/liuqichun3809/Quantum_Lab/issues',
        'Source': 'https://github.com/liuqichun3809/Quantum_Lab/',
    },
)

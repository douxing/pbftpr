import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s*=\s*(.*)')

with open('pbft/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

_install_requires = [
    'click',
    'coincurve',
    'rlp',
    'toml',
]

setup(
    name = 'pbft',
    author = 'dx',
    author_email = 'douxing1983@outlook.com',
    version = version,
    url = 'https://github.com/douxing/pypbft',
    packages = ['pbft'],
    entry_points = {
        'console_scripts': [
            'pbft=pbft:cli_main'
        ]
    },
    install_requires = _install_requires,
    description = 'a humble implementation of pbft-pr',
    classifiers = [
        "License :: MIT",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',        
    ]
)

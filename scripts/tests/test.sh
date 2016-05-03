#!/bin/bash
cd ..
echo "flake8"
flake8 endpoint_check.py
echo "pyflakes"
pyflakes endpoint_check.py
echo "pytest"
py.test -v --cov endpoint_check.py test_endpoint_check.py 

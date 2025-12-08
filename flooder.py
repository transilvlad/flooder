#!/usr/bin/env python3
"""
Top-level shim for the refactored `flooder` package.
This file keeps backwards compatibility for `python flooder.py` while the
real implementation lives in the `flooder` package.
"""
from flooder.flooder import main

if __name__ == '__main__':
    main()

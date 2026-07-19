# -*- coding: utf-8 -*-
"""
Handles hyde version.

The version is defined in pyproject.toml and read from the installed
package metadata.
"""
from importlib.metadata import version

__version__ = version("hyde")

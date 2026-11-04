"""Compatibility entry point selecting one of two separate lab APIs."""
import os

from .after import issue_token
from .before import create_app as create_before_app
from .after import create_app as create_fixed_app

def create_app(mode="fixed"):
    if mode == "before":
        return create_before_app()
    if mode == "fixed":
        return create_fixed_app()
    raise ValueError(f"Unknown lab mode: {mode}")

app = create_app(os.getenv("LAB_MODE", "fixed"))

"""Render module package."""

from modules.render.escape import escape_html
from modules.render.paragraph import render_plain_paragraph

__all__ = ["escape_html", "render_plain_paragraph"]

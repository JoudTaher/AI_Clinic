"""Agreement template catalog and deterministic matching rules."""

from src.templates.catalog import CatalogError, TemplateDefinition, load_template_catalog
from src.templates.selector import select_template

__all__ = [
    "CatalogError",
    "TemplateDefinition",
    "load_template_catalog",
    "select_template",
]

"""
backend/sitemap_app/schemas/__init__.py
Pydantic v2 schemas for Sitemaps, Wireframes, and Requirement Briefs.
"""

from .sitemap import (
    BriefContextModel,
    SitemapSectionModel,
    SitemapPageModel,
    SitemapModel,
    validate_sitemap,
    repair_sitemap,
    SUPPORTED_SECTION_TYPES,
    SECTION_TYPE_ALIASES,
)

from .wireframe import (
    SectionItemModel,
    SectionStylesModel,
    ResponsiveSettingsModel,
    WireframeSectionModel,
    PageWireframeModel,
    WireframeContainerModel,
    SUPPORTED_LAYOUT_VARIANTS,
    LAYOUT_VARIANT_ALIASES,
    DEFAULT_ITEMS_BY_SECTION_TYPE,
    repair_wireframe_item,
    repair_wireframe_section,
    repair_page_wireframe,
    repair_wireframe_container,
    validate_wireframe,
    validate_page_wireframe,
)

__all__ = [
    # Sitemap
    "BriefContextModel",
    "SitemapSectionModel",
    "SitemapPageModel",
    "SitemapModel",
    "validate_sitemap",
    "repair_sitemap",
    "SUPPORTED_SECTION_TYPES",
    "SECTION_TYPE_ALIASES",
    # Wireframe
    "SectionItemModel",
    "SectionStylesModel",
    "ResponsiveSettingsModel",
    "WireframeSectionModel",
    "PageWireframeModel",
    "WireframeContainerModel",
    "SUPPORTED_LAYOUT_VARIANTS",
    "LAYOUT_VARIANT_ALIASES",
    "DEFAULT_ITEMS_BY_SECTION_TYPE",
    "repair_wireframe_item",
    "repair_wireframe_section",
    "repair_page_wireframe",
    "repair_wireframe_container",
    "validate_wireframe",
    "validate_page_wireframe",
]

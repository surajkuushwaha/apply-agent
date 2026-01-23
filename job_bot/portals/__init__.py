"""
Portal handlers for different job platforms.

Each portal implements the BasePortal interface for consistent behavior.
"""

from .base import BasePortal
from .linkedin import LinkedInPortal
from .workatastartup import WorkAtAStartupPortal

__all__ = [
    "BasePortal",
    "LinkedInPortal",
    "WorkAtAStartupPortal",
]

# Registry of available portals
PORTAL_REGISTRY = {
    "linkedin": LinkedInPortal,
    "workatastartup": WorkAtAStartupPortal,
}


def get_portal(portal_key: str) -> BasePortal:
    """Get a portal instance by key."""
    if portal_key not in PORTAL_REGISTRY:
        raise ValueError(f"Unknown portal: {portal_key}. Available: {list(PORTAL_REGISTRY.keys())}")
    return PORTAL_REGISTRY[portal_key]()

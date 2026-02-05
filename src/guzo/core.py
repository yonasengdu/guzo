"""Shared utilities and constants for Guzo."""

from pydantic import BaseModel


# ============== Common Response Models ==============

class DeleteResponse(BaseModel):
    """Response for successful delete operations."""
    status: str = "deleted"
    message: str = "Resource deleted successfully"


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: str = ""


# ============== Ethiopian Locations ==============

# Ethiopian cities for trip origin/destination selection
LOCATIONS = [
    'Addis Ababa',
    'Adama (Nazret)',
    'Dire Dawa',
    'Mekelle',
    'Gondar',
    'Hawassa',
    'Bahir Dar',
    'Dessie',
    'Jimma',
    'Jijiga',
    'Shashamane',
    'Bishoftu (Debre Zeit)',
    'Arba Minch',
    'Hosaena',
    'Harar',
    'Dilla',
    'Nekemte',
    'Goba',
    'Sodo',
    'Asella',
    'Debre Markos',
    'Kombolcha',
    'Lalibela',
    'Axum',
]

# Sort locations alphabetically
LOCATIONS.sort()


"""
Database Schemas for Empty Leg Flights App

Each Pydantic model represents a collection in MongoDB. The collection name
is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Emptylegflight(BaseModel):
    """
    Empty leg flight listing
    Collection name: "emptylegflight"
    """
    operator: str = Field(..., description="Operator name")
    aircraft_type: str = Field(..., description="Aircraft type")
    origin: str = Field(..., description="Origin airport code (IATA)")
    origin_city: Optional[str] = Field(None, description="Origin city")
    destination: str = Field(..., description="Destination airport code (IATA)")
    destination_city: Optional[str] = Field(None, description="Destination city")
    departure_time: datetime = Field(..., description="Scheduled departure (UTC)")
    arrival_time: datetime = Field(..., description="Scheduled arrival (UTC)")
    seats_available: int = Field(..., ge=0, description="Available seats")
    price: float = Field(..., ge=0, description="Quoted price for entire leg (USD)")
    currency: str = Field("USD", description="Currency code")
    notes: Optional[str] = Field(None, description="Extra details or restrictions")

class Booking(BaseModel):
    """
    Booking request for an empty leg
    Collection name: "booking"
    """
    flight_id: str = Field(..., description="Referenced empty leg flight _id as string")
    name: str = Field(..., description="Primary passenger full name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    passengers: int = Field(..., ge=1, description="Number of passengers")
    notes: Optional[str] = Field(None, description="Additional notes")
    status: str = Field("confirmed", description="Booking status")

# Keeping an example simple user for potential future expansion
class User(BaseModel):
    name: str
    email: str
    is_active: bool = True

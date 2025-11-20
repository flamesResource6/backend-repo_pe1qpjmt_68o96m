import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Emptylegflight, Booking

app = FastAPI(title="Empty Leg Flights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Empty Leg Flights API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Helper to convert Mongo _id to string

def serialize_doc(doc: dict):
    if doc is None:
        return None
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert datetimes to isoformat
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d

# Seed route (optional, for demo)
@app.post("/api/seed")
def seed_data():
    sample = Emptylegflight(
        operator="SkyJet",
        aircraft_type="Citation XLS+",
        origin="LAS",
        origin_city="Las Vegas",
        destination="VNY",
        destination_city="Los Angeles",
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow(),
        seats_available=6,
        price=8900,
        currency="USD",
        notes="Flexible within +/- 6 hours"
    )
    inserted_id = create_document("emptylegflight", sample)
    return {"inserted_id": inserted_id}

# Public: list and search empty legs
@app.get("/api/flights")
def list_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50
):
    filt = {}
    if origin:
        filt["origin"] = origin.upper()
    if destination:
        filt["destination"] = destination.upper()
    if date:
        # match departure date (UTC) yyyy-mm-dd
        try:
            start = datetime.fromisoformat(date)
            end = datetime.fromisoformat(date) .replace(hour=23, minute=59, second=59)
            filt["departure_time"] = {"$gte": start, "$lte": end}
        except Exception:
            pass
    docs = get_documents("emptylegflight", filt, limit)
    return [serialize_doc(d) for d in docs]

class BookingIn(BaseModel):
    flight_id: str
    name: str
    email: str
    phone: Optional[str] = None
    passengers: int
    notes: Optional[str] = None

# Create a booking
@app.post("/api/book")
def create_booking(payload: BookingIn):
    # Validate flight exists
    try:
        oid = ObjectId(payload.flight_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid flight_id")

    flight = db["emptylegflight"].find_one({"_id": oid})
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    if payload.passengers < 1 or payload.passengers > flight.get("seats_available", 0):
        raise HTTPException(status_code=400, detail="Invalid passengers count")

    booking = Booking(
        flight_id=str(oid),
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        passengers=payload.passengers,
        notes=payload.notes,
        status="pending"
    )
    booking_id = create_document("booking", booking)

    # Reduce available seats
    db["emptylegflight"].update_one({"_id": oid}, {"$inc": {"seats_available": -payload.passengers}})

    return {"booking_id": booking_id, "status": "pending"}

# Admin: create flight listing
@app.post("/api/flights")
def create_flight(flight: Emptylegflight):
    inserted_id = create_document("emptylegflight", flight)
    return {"id": inserted_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

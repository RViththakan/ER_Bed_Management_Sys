from pydantic import BaseModel

class PatientInput(BaseModel):
    age: int
    condition: str
    ctas_level: str
    nurse_ratio: int
    specialist_availability: int
    region: str
    hospital: str

# NEW: For assigning housekeeping staff
class TicketUpdate(BaseModel):
    ticket_id: str
    staff_name: str
    status: str
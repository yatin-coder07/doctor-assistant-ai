from pydantic import BaseModel

class BookRequest(BaseModel):
    slot: str
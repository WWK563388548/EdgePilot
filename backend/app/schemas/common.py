from pydantic import BaseModel


class CountResponse(BaseModel):
    total: int

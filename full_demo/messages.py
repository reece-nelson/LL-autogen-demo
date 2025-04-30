from pydantic import BaseModel

class RequestMsg(BaseModel):
    request: str

class VacationSpecificationMsg(RequestMsg):
    specification: str

class VacationBudgetMsg(VacationSpecificationMsg):
    budget:str

class VacationItineraryMsg(VacationBudgetMsg):
    itinerary:str
from pydantic import BaseModel

class PreparationBody(BaseModel):
    food_list: list[str]


class PromptBody(BaseModel):
    food_list: list[str]
    spices: list[str]
    narrative: str

class GenAIResponse(BaseModel):
    status: str
    message: str
    payload: str | dict
    
    class Config:
        from_attributes = True
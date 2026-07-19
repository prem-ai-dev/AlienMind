from pydantic import BaseModel,Field,field_validator,ConfigDict
from datetime import datetime

class UserInput(BaseModel):
    name:str
    email:str
    password:str

class UserValidation(BaseModel):
    user_id:str=Field(alias="_id")
    name:str
    email:str
    password:str
    created_at:datetime

    model_config=ConfigDict(populate_by_name=True)

    @field_validator("user_id",mode="before")
    @classmethod

    def convert(cls,v):
        return str(v)
from pydantic import BaseModel

class TempTokenData(BaseModel):
    user_id:str
    email:str

class LongTokenData(BaseModel):
    workspace_id:str
    user_id:str
    role:str
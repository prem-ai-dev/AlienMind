from pydantic import BaseModel,EmailStr
from datetime import datetime

class CreateUserInput(BaseModel):
    name: str
    email: EmailStr
    password: str

class NewUserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    created_at: datetime

class FreshSignupInput(BaseModel):
    username:str
    company_name:str

class DomainSignupInput(BaseModel):
    workspace_id: str
    username: str

class CreateUserResponse(BaseModel):
    access_token:str
    token_type:str
    user:NewUserResponse

class SignupResponse(BaseModel):
    workspace_id:str
    user_id:str
    username:str
    role:str
    joined_at:datetime

class FreshSignupResponse(BaseModel):
    access_token:str
    token_type:str
    data:SignupResponse

class WorkspaceOption(BaseModel):
    workspace_id: str
    company_name: str

class DomainLookupResponse(BaseModel):
    workspaces: list[WorkspaceOption]
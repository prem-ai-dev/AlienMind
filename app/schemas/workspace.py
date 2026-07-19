from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field,field_validator
from app.schemas.signup import SignupResponse

class CreateWorkspaceInput(BaseModel):
    username:str
    company_name:str

class AddDomainInput(BaseModel):
    domain:str

class WorkspaceValidate(BaseModel):
    workspace_id:str=Field(alias="_id")
    company_name:str
    created_at:datetime
    owner_ids:list[str]=Field(default_factory=list)
    team_ids:list[str]=Field(default_factory=list)
    project_ids:list[str]=Field(default_factory=list)
    member_ids:list[str]=Field(default_factory=list)
    allowed_domains:list[str]=Field(default_factory=list)

    model_config=ConfigDict(populate_by_name=True)

    @field_validator("workspace_id",mode="before")
    @classmethod
    def convert(cls,v):
        return str(v)
    
class WorkspaceResponse(BaseModel):
    workspace_id:str
    company_name:str
    allowed_domains:list[str]=Field(default_factory=list)
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

class CreateWorkspaceResponse(BaseModel):
    access_token: str
    token_type: str
    data: SignupResponse

class WorkspaceList(BaseModel):
    workspace_id:str
    company_name:str
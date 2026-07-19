from pydantic import BaseModel,Field
from datetime import datetime

class Workspace(BaseModel):

    company_name:str
    created_at:datetime
    owner_ids:list[str]=Field(default_factory=list)
    team_ids:list[str]=Field(default_factory=list)
    project_ids:list[str]=Field(default_factory=list)
    member_ids:list[str]=Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
from pydantic import BaseModel
from app.schemas.workspace import WorkspaceList

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    workspace_list: list[WorkspaceList]
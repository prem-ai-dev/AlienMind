from fastapi import APIRouter,Depends
from app.services.login_service import LoginService
from app.core.dependencies import get_login_service
from app.core.auth import create_token
from app.schemas.login import LoginResponse
from app.schemas.login import LoginRequest
from app.core.enum import TokenTime
from app.schemas.token_data import TempTokenData
from app.core.dependencies import get_temp_user_data

router=APIRouter(prefix="/auth",tags=["AUTH"])

@router.post("/login",response_model=LoginResponse)
async def login_verify(
    data:LoginRequest,
    login_manager:LoginService=Depends(get_login_service)
):
    result,workspace_list= await login_manager.verify_login(email=data.email,password=data.password)
    token=create_token(
        data={
            "user_id":result.user_id,
            "email":result.email
        },
        minutes=TokenTime.temp_token.value
    )
    return {
        "access_token":token,
        "token_type":"bearer",
        "workspace_list": [
            {
                "workspace_id": w.workspace_id,
                "company_name": w.company_name
            }
            for w in workspace_list
        ]
    }

@router.post("/select_workspace/{workspace_id}")
async def token_with_workspace(
    workspace_id:str,
    token_data:TempTokenData=Depends(get_temp_user_data),
    login_manager:LoginService=Depends(get_login_service)
):
    result=await login_manager.verify_membership(workspace_id=workspace_id,user_id=token_data.user_id)
    token=create_token(
        data={
            "workspace_id":workspace_id,
            "user_id":token_data.user_id,
            "role":result["role"]
        },
        minutes=TokenTime.long_token.value
    )

    return {
        "access_token":token,
        "token_type":"bearer"
    }
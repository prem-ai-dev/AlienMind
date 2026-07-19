from fastapi import APIRouter,Depends
from app.services.signup_service import SignupService
from app.schemas.token_data import TempTokenData
from app.core.dependencies import get_signup_service,get_temp_user_data
from app.schemas.signup import (
    CreateUserInput,
    CreateUserResponse,
    FreshSignupInput,
    FreshSignupResponse,
    DomainSignupInput,
    DomainLookupResponse
)
from app.core.auth import create_token
from app.core.enum import TokenTime

router = APIRouter(prefix="/signup", tags=["signup"])

@router.post("/new_user", response_model=CreateUserResponse)
async def create_fresh_user_route(
    data: CreateUserInput,
    signup_manager:SignupService=Depends(get_signup_service)
    ):
    result= await signup_manager.create_fresh_user(
        name=data.name,
        email=data.email,
        password=data.password,
    )
    temp_token=create_token(
        data={
            "user_id":result.user_id,
            "email":result.email
        },
        minutes=TokenTime.temp_token.value
    )
    return {
        "access_token":temp_token,
        "token_type":"bearer",
        "user":result
    }

@router.post("/fresh_signup", response_model=FreshSignupResponse)
async def fresh_signup_route(
    data: FreshSignupInput,
    signup_manager:SignupService=Depends(get_signup_service),
    user_data:TempTokenData=Depends(get_temp_user_data)
    ):
    result= await signup_manager.fresh_signup(
        user_id=user_data.user_id,
        username=data.username,
        email=user_data.email,
        company_name=data.company_name,
    )
    token=create_token(
        data={
            "workspace_id":result.workspace_id,
            "user_id":result.user_id,
            "role":result.role
        },
        minutes=TokenTime.long_token.value
    )
    return {
        "access_token":token,
        "token_type":"bearer",
        "data":result
    }

@router.get("/domain/lookup",response_model=DomainLookupResponse)
async def domain_lookup_route(
    signup_manager:SignupService=Depends(get_signup_service),
    user_data:TempTokenData=Depends(get_temp_user_data)
):
    result=await signup_manager.get_workspaces_for_domain(
        email=user_data.email
        )
    return result

@router.post("/domain_signup",response_model=FreshSignupResponse)
async def domain_signup_route(
    data: DomainSignupInput,
    signup_manager:SignupService=Depends(get_signup_service),
    user_data:TempTokenData=Depends(get_temp_user_data)
    ):
        result=await signup_manager.domain_signup(
            email=user_data.email,
            workspace_id=data.workspace_id,
            username=data.username,
        )
        token=create_token(
            data={
                "workspace_id":result.workspace_id,
                "user_id":result.user_id,
                "role":result.role
            },
            minutes=TokenTime.long_token.value
        )
        return {
            "access_token":token,
            "token_type":"bearer",
            "data":result
        }
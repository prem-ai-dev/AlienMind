from app.core.enum import Role, ROLE_RANK
from app.schemas.workspace_member import WorkspaceMemberValidate
from app.database.repositories.workspace_member_repository import find_workspace_member
from app.core.exception import NotFoundError,MinimumClreanceError

async def verify_role(workspace_id: str, user_id: str, min_role: Role):
    member = await find_workspace_member(
        workspace_id=workspace_id,
        user_id=user_id
    )

    if member is None:
        raise NotFoundError(f"user_id: {user_id} not found in workspace_id: {workspace_id}")

    validated_member = WorkspaceMemberValidate.model_validate(member)

    if ROLE_RANK[validated_member.role] < ROLE_RANK[min_role]:
        raise MinimumClreanceError(f"user_id: {user_id} role={validated_member.role} does not meet required role: {min_role}")

    return validated_member
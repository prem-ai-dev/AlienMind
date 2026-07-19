from enum import Enum

class ProjectStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"

class SprintStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CANCELLED="CANCELLED"

class TeamStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"

class WorkspaceMemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"

class CollectionNames(str, Enum):
    tasks="tasks"
    sprints="sprints"
    projects="projects"
    teams="teams"
    users="users"
    workspaces="workspaces"
    workspace_members="workspace-members"    

class TokenTime(int, Enum):
    temp_token=5
    long_token=60

class Role(str, Enum):
    MEMBER ="MEMBER"
    MANAGER="MANAGER"
    COMPANY_ADMIN ="COMPANY_ADMIN"

ROLE_RANK={
            Role.MEMBER.value:1,
            Role.MANAGER.value:2,
            Role.COMPANY_ADMIN.value:3
        }
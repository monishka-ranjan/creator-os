import uuid

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class MembershipOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: str
    role: str = Field(pattern="^(owner|manager|editor|viewer)$")
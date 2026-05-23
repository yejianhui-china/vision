# ========================================================
# 角色权限管理模块
# 文件: backend/app/routers/roles.py
# ========================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Role, Page, RolePagePermission

router = APIRouter(tags=["角色管理"])


# ========================================================
# Pydantic 模型
# ========================================================

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    total: int
    items: List[RoleResponse]


class PageResponse(BaseModel):
    id: int
    code: str
    name: str
    path: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


class RolePagesUpdate(BaseModel):
    page_ids: List[int] = Field(..., description="页面ID列表")


class RoleDetailResponse(RoleResponse):
    pages: List[PageResponse] = []


# ========================================================
# API 接口
# ========================================================

@router.get("/api/roles", response_model=RoleListResponse)
def list_roles(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """角色列表（分页）"""
    query = db.query(Role)
    total = query.count()
    items = query.order_by(Role.sort_order.asc(), Role.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.post("/api/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role_in: RoleCreate, db: Session = Depends(get_db)):
    """创建角色"""
    if db.query(Role).filter(Role.name == role_in.name).first():
        raise HTTPException(status_code=400, detail="角色名称已存在")
    if db.query(Role).filter(Role.code == role_in.code).first():
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role = Role(
        name=role_in.name,
        code=role_in.code,
        description=role_in.description
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/api/roles/{role_id}", response_model=RoleDetailResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """获取角色详情（含页面权限）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    pages = [rp.page for rp in role.permissions]
    result = RoleDetailResponse.model_validate(role)
    result.pages = [PageResponse.model_validate(p) for p in pages]
    return result


@router.put("/api/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_in: RoleUpdate, db: Session = Depends(get_db)):
    """更新角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role


@router.delete("/api/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """删除角色（同时清理关联权限）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 清理关联权限
    db.query(RolePagePermission).filter(RolePagePermission.role_id == role_id).delete()

    db.delete(role)
    db.commit()
    return {"message": "角色已删除"}


@router.get("/api/roles/pages/all", response_model=List[PageResponse])
def list_all_pages(db: Session = Depends(get_db)):
    """获取所有页面"""
    pages = db.query(Page).order_by(Page.sort_order.asc(), Page.id.asc()).all()
    return pages


@router.put("/api/roles/{role_id}/pages")
def update_role_pages(role_id: int, data: RolePagesUpdate, db: Session = Depends(get_db)):
    """更新角色页面权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证所有页面ID有效
    if data.page_ids:
        existing_pages = db.query(Page).filter(Page.id.in_(data.page_ids)).all()
        existing_ids = {p.id for p in existing_pages}
        invalid_ids = set(data.page_ids) - existing_ids
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"无效的页面ID: {invalid_ids}")

    # 删除旧权限
    db.query(RolePagePermission).filter(RolePagePermission.role_id == role_id).delete()

    # 添加新权限
    for page_id in data.page_ids:
        rp = RolePagePermission(role_id=role_id, page_id=page_id)
        db.add(rp)

    db.commit()
    return {"message": "权限已更新"}


@router.get("/api/users/roles", response_model=List[dict])
def get_user_role_options(db: Session = Depends(get_db)):
    """获取角色选项列表（用于下拉框）"""
    roles = db.query(Role).filter(Role.is_active == True).order_by(Role.sort_order.asc()).all()
    return [{"value": role.id, "label": role.name, "code": role.code} for role in roles]

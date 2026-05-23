# ========================================================
# FastAPI 用户管理模块
# 文件: backend/app/routers/users.py
# ========================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import bcrypt

from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/users", tags=["用户管理"])


# ========================================================
# Pydantic 数据模型（请求/响应校验）
# ========================================================

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=2, max_length=50, description="登录账号")
    name: str = Field(..., min_length=1, max_length=50, description="显示姓名")
    role: str = Field(..., pattern="^(designer|reviewer|approver|admin)$", description="角色")
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)
    is_active: bool = Field(True, description="是否启用")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=4, max_length=100, description="初始密码")


class UserUpdate(BaseModel):
    """更新用户请求（全部可选）"""
    name: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, pattern="^(designer|reviewer|approver|admin)$")
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=4, max_length=100, description="留空则不修改密码")


class UserResponse(UserBase):
    """用户响应（不含密码）"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: List[UserResponse]


# ========================================================
# 工具函数
# ========================================================

def hash_password(password: str) -> str:
    """密码 bcrypt 哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ========================================================
# API 接口
# ========================================================

@router.get("", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    department: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    - skip/limit: 分页
    - role: 按角色筛选
    - department: 按部门筛选
    - keyword: 模糊搜索用户名/姓名/邮箱
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if department:
        query = query.filter(User.department == department)
    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (User.username.ilike(search)) |
            (User.name.ilike(search)) |
            (User.email.ilike(search))
        )
    
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "items": items}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取单个用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """创建新用户"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在（如有填写）
    if user_in.email and db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 创建用户
    user = User(
        username=user_in.username,
        password=hash_password(user_in.password),
        name=user_in.name,
        role=user_in.role,
        email=user_in.email,
        phone=user_in.phone,
        department=user_in.department,
        is_active=user_in.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段（只更新传入的非空值）
    update_data = user_in.model_dump(exclude_unset=True)
    
    # 如果更新了密码，需要重新哈希
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    else:
        update_data.pop("password", None)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户（物理删除，生产环境建议改为软删除）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 禁止删除最后一个管理员
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="不能删除唯一的系统管理员")
    
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


@router.post("/{user_id}/toggle-status")
def toggle_user_status(user_id: int, db: Session = Depends(get_db)):
    """切换用户启用/禁用状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 禁止禁用最后一个管理员
    if user.role == "admin" and user.is_active:
        active_admin_count = db.query(User).filter(
            User.role == "admin", User.is_active == True, User.id != user_id
        ).count()
        if active_admin_count == 0:
            raise HTTPException(status_code=400, detail="不能禁用唯一的系统管理员")
    
    user.is_active = not user.is_active
    db.commit()
    
    status_text = "启用" if user.is_active else "禁用"
    return {"message": f"用户已{status_text}", "is_active": user.is_active}

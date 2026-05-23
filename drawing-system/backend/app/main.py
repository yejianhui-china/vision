# ========================================================# FastAPI 主入口# 文件: backend/app/main.py# ========================================================

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt

from .database import init_db, get_db
from .routers import users, designer, product_models, bom, roles
from .models import User

app = FastAPI(
    title="生产管理系统 API",
    description="内网图纸存储、审批、BOM管理",
    version="1.0.0",
)

# 跨域配置（开发阶段允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router)
app.include_router(designer.router)
app.include_router(product_models.router)
app.include_router(bom.router)
app.include_router(roles.router)

# 启动时自动建表（仅开发阶段，生产用 Alembic 迁移）
@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "生产管理系统 API 运行中", "docs": "/docs"}


class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not bcrypt.checkpw(body.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    
    # 获取用户的页面权限
    from .models import Role, Page, RolePagePermission
    pages = []
    if user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role and role.code == "admin":
            pages = db.query(Page).filter(Page.is_active == True).all()
        else:
            pages = db.query(Page).join(
                RolePagePermission, Page.id == RolePagePermission.page_id
            ).filter(RolePagePermission.role_id == user.role_id, Page.is_active == True).all()
    
    page_list = [{"id": p.id, "code": p.code, "name": p.name, "path": p.path, "icon": p.icon} for p in pages]
    
    # 生成简单 token（实际生产环境应使用 JWT）
    import base64
    token = base64.b64encode(f"{user.username}:{user.id}".encode()).decode()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "pages": page_list
        }
    }

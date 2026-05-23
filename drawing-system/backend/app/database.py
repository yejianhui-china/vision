# ========================================================# 数据库连接配置# 文件: backend/app/database.py# ========================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# 数据库连接URL，从环境变量读取，默认本地开发配置
# 格式: postgresql://用户名:密码@主机:端口/数据库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Y15JX621%40@localhost:5432/drawing_system"
)

# 创建引擎
engine = create_engine(DATABASE_URL)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 模型基类
Base = declarative_base()


def get_db() -> Session:
    """FastAPI Dependency: 获取数据库会话，请求结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表（开发阶段用）"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from .models import Role, Page, RolePagePermission

        # 初始化默认角色
        if db.query(Role).count() == 0:
            default_roles = [
                Role(code="sales", name="销售员", description="销售员", sort_order=1),
                Role(code="warehouse", name="仓库管理员", description="仓库管理员", sort_order=2),
                Role(code="planner", name="生产计划管理员", description="生产计划管理员", sort_order=3),
                Role(code="admin", name="系统管理员", description="系统管理员", sort_order=4),
                Role(code="mechanical", name="机械结构工程师", description="机械结构工程师", sort_order=5),
                Role(code="operator", name="生产操作员", description="生产操作员", sort_order=6),
                Role(code="iqc", name="IQC检验", description="IQC检验", sort_order=7),
                Role(code="purchaser", name="采购员", description="采购员", sort_order=8),
            ]
            for role in default_roles:
                db.add(role)
            db.commit()

        # 初始化默认页面
        if db.query(Page).count() == 0:
            default_pages = [
                Page(code="users", name="系统管理", path="/users", sort_order=1),
                Page(code="designer", name="销售预测管理", path="/designer", sort_order=2),
                Page(code="bom", name="BOM管理", path="/bom", sort_order=3),
            ]
            for page in default_pages:
                db.add(page)
            db.commit()

        # 初始化权限（所有角色拥有所有页面）
        if db.query(RolePagePermission).count() == 0:
            roles = db.query(Role).all()
            pages = db.query(Page).all()
            for role in roles:
                for page in pages:
                    db.add(RolePagePermission(role_id=role.id, page_id=page.id))
            db.commit()
    finally:
        db.close()

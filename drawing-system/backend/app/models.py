# ========================================================
# SQLAlchemy 数据模型
# 文件: backend/app/models.py
# ========================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON, UniqueConstraint, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String(50), unique=True, nullable=False, index=True)
    password    = Column(String(255), nullable=False)
    name        = Column(String(50), nullable=False)
    role        = Column(String(20), nullable=False, index=True)
    role_id     = Column(Integer, ForeignKey("roles.id"), nullable=True, comment="角色ID")
    email       = Column(String(100), nullable=True)
    phone       = Column(String(20), nullable=True)
    department  = Column(String(50), nullable=True, index=True)
    is_active   = Column(Boolean, default=True, index=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role_obj    = relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}', role='{self.role}')>"


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50), unique=True, nullable=False, comment="角色编码")
    name        = Column(String(50), nullable=False, comment="角色名称")
    description = Column(Text, nullable=True, comment="描述")
    is_active   = Column(Boolean, default=True, comment="是否启用")
    sort_order  = Column(Integer, default=0, comment="排序")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users       = relationship("User", back_populates="role_obj")
    permissions = relationship("RolePagePermission", back_populates="role", cascade="all, delete-orphan")


class Page(Base):
    """页面/菜单表"""
    __tablename__ = "pages"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50), unique=True, nullable=False, comment="页面编码")
    name        = Column(String(50), nullable=False, comment="页面名称")
    path        = Column(String(200), nullable=True, comment="页面路径")
    icon        = Column(String(100), nullable=True, comment="图标")
    description = Column(Text, nullable=True, comment="描述")
    is_active   = Column(Boolean, default=True, comment="是否启用")
    sort_order  = Column(Integer, default=0, comment="排序")

    permissions = relationship("RolePagePermission", back_populates="page", cascade="all, delete-orphan")


class RolePagePermission(Base):
    """角色页面权限关联表"""
    __tablename__ = "role_page_permissions"

    id      = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID")
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, comment="页面ID")

    __table_args__ = (
        UniqueConstraint("role_id", "page_id", name="uix_role_page"),
    )

    role = relationship("Role", back_populates="permissions")
    page = relationship("Page", back_populates="permissions")


class Part(Base):
    """料号/零件表"""
    __tablename__ = "parts"

    id          = Column(Integer, primary_key=True, index=True)
    part_number = Column(String(50), unique=True, nullable=False, index=True, comment="料号")
    name        = Column(String(100), nullable=False, comment="名称")
    spec        = Column(String(200), nullable=True, comment="规格")
    type        = Column(String(20), default="part", nullable=True, comment="类型: product/semi_product/component/part")
    unit        = Column(String(20), nullable=True, comment="单位")
    description = Column(Text, nullable=True, comment="描述")
    designer_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人")
    status      = Column(String(20), default="draft", nullable=False, comment="状态: draft/approved/obsoleted")
    extra_data  = Column(JSON, default=dict, comment="扩展字段")
    approval_status = Column(String(20), default="draft", nullable=False, comment="审批状态")
    nature_code = Column(String(10), nullable=True, comment="性质编码")
    category_code = Column(String(10), nullable=True, comment="大类编码")
    subcategory_code = Column(String(10), nullable=True, comment="小类编码")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    designer    = relationship("User")
    drawings    = relationship("Drawing", back_populates="part", cascade="all, delete-orphan")
    prototypes  = relationship("PrototypeRequest", back_populates="part", cascade="all, delete-orphan")
    children    = relationship(
        "BomRelation",
        foreign_keys="BomRelation.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    parents     = relationship(
        "BomRelation",
        foreign_keys="BomRelation.child_id",
        back_populates="child",
        cascade="all, delete-orphan"
    )


class Drawing(Base):
    """图纸表"""
    __tablename__ = "drawings"

    id           = Column(Integer, primary_key=True, index=True)
    part_id      = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="关联料号")
    file_name    = Column(String(255), nullable=False, comment="原始文件名")
    file_path    = Column(String(500), nullable=False, comment="存储路径")
    version      = Column(String(20), default="V1.0", nullable=False, comment="版本号")
    uploaded_by  = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传人")
    remark       = Column(Text, nullable=True, comment="备注")
    uploaded_at  = Column(DateTime(timezone=True), server_default=func.now())

    part         = relationship("Part", back_populates="drawings")
    uploader     = relationship("User")


class PrototypeRequest(Base):
    """打样申请表"""
    __tablename__ = "prototype_requests"

    id            = Column(Integer, primary_key=True, index=True)
    part_id       = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="关联料号")
    quantity      = Column(Integer, default=1, nullable=False, comment="数量")
    reason        = Column(Text, nullable=False, comment="申请原因")
    status        = Column(String(20), default="pending", nullable=False, comment="状态: pending/reviewing/approved/rejected")
    requested_by  = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人")
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    part          = relationship("Part", back_populates="prototypes")
    requester     = relationship("User")


class BomRelation(Base):
    """BOM父子关系表"""
    __tablename__ = "bom_relations"

    id         = Column(Integer, primary_key=True, index=True)
    parent_id  = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="父件ID")
    child_id   = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="子件ID")
    quantity   = Column(Integer, default=1, nullable=False, comment="用量")
    sort_order = Column(Integer, default=0, comment="排序")

    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", name="uix_bom_relation"),
        CheckConstraint("parent_id != child_id", name="ck_bom_no_self_ref"),
    )

    parent = relationship("Part", foreign_keys=[parent_id], back_populates="children")
    child  = relationship("Part", foreign_keys=[child_id], back_populates="parents")


class PartNumberCounter(Base):
    """料号序号计数器"""
    __tablename__ = "part_number_counters"

    id             = Column(Integer, primary_key=True, index=True)
    category_code  = Column(String(20), unique=True, nullable=False, comment="分类编码")
    last_sequence  = Column(Integer, default=0, nullable=False, comment="最后序号")
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProductModel(Base):
    """产品型号表"""
    __tablename__ = "product_models"

    id            = Column(Integer, primary_key=True, index=True)
    product_code  = Column(String(50), unique=True, nullable=False, index=True, comment="产品编码")
    product_name  = Column(String(100), nullable=False, comment="产品名称")
    spec_model    = Column(String(200), nullable=True, comment="规格型号")
    unit          = Column(String(20), nullable=True, comment="单位")
    description   = Column(Text, nullable=True, comment="备注")
    is_active     = Column(Boolean, default=True, index=True, comment="是否启用")
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ========================================================
# BOM 管理模块
# 文件: backend/app/routers/bom.py
# ========================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Part, BomRelation

router = APIRouter(prefix="/api/bom", tags=["BOM管理"])


# ========================================================
# Pydantic 模型
# ========================================================

class PartBase(BaseModel):
    id: int
    part_number: str
    name: str
    type: Optional[str]
    spec: Optional[str]
    unit: Optional[str]

    class Config:
        from_attributes = True


class BomTreeItem(BaseModel):
    id: int
    part: PartBase
    quantity: int
    children: List["BomTreeItem"] = []

    class Config:
        from_attributes = True


BomTreeItem.model_rebuild()


class BomTreeResponse(BaseModel):
    part: PartBase
    tree: List[BomTreeItem]


class BomCreate(BaseModel):
    parent_id: int = Field(..., description="父件ID")
    child_id: int = Field(..., description="子件ID")
    quantity: int = Field(default=1, ge=1, description="数量")


class BomUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="数量")


class MaterialListResponse(BaseModel):
    total: int
    items: List[PartBase]


# ========================================================
# 工具函数
# ========================================================

TYPE_ORDER = {
    "product": 1,
    "semi_product": 2,
    "component": 3,
    "part": 4,
}


def validate_bom_hierarchy(parent_type: Optional[str], child_type: Optional[str]):
    """校验 BOM 层级：product < semi_product < component < part"""
    if parent_type not in TYPE_ORDER or child_type not in TYPE_ORDER:
        raise HTTPException(status_code=400, detail="父件或子件类型无效")
    if TYPE_ORDER[parent_type] >= TYPE_ORDER[child_type]:
        raise HTTPException(
            status_code=400,
            detail="层级校验失败：父件类型必须高于子件类型（product < semi_product < component < part）"
        )


def build_bom_tree(db: Session, parent_id: int, visited: Optional[set] = None) -> List[BomTreeItem]:
    """递归构建 BOM 树"""
    if visited is None:
        visited = set()

    if parent_id in visited:
        return []

    visited.add(parent_id)

    items = db.query(BomRelation).filter(BomRelation.parent_id == parent_id).all()
    result = []
    for item in items:
        child = db.query(Part).filter(Part.id == item.child_id).first()
        if not child:
            continue
        children = build_bom_tree(db, item.child_id, visited.copy())
        result.append(BomTreeItem(
            id=item.id,
            part=PartBase(
                id=child.id,
                part_number=child.part_number,
                name=child.name,
                type=child.type,
                spec=child.spec,
                unit=child.unit
            ),
            quantity=item.quantity,
            children=children
        ))
    return result


# ========================================================
# API 接口
# ========================================================

@router.get("/materials", response_model=MaterialListResponse)
def list_materials(
    type: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """物料列表（支持 type/keyword 筛选）"""
    query = db.query(Part)

    if type:
        query = query.filter(Part.type == type)
    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (Part.part_number.ilike(search)) |
            (Part.name.ilike(search))
        )

    total = query.count()
    items = query.order_by(Part.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_bom(bom_in: BomCreate, db: Session = Depends(get_db)):
    """创建 BOM 关系（校验层级：product < semi_product < component < part）"""
    parent = db.query(Part).filter(Part.id == bom_in.parent_id).first()
    child = db.query(Part).filter(Part.id == bom_in.child_id).first()

    if not parent:
        raise HTTPException(status_code=404, detail="父件不存在")
    if not child:
        raise HTTPException(status_code=404, detail="子件不存在")
    if parent.id == child.id:
        raise HTTPException(status_code=400, detail="父件和子件不能相同")

    validate_bom_hierarchy(parent.type, child.type)

    # 检查是否已存在
    existing = db.query(BomRelation).filter(
        BomRelation.parent_id == bom_in.parent_id,
        BomRelation.child_id == bom_in.child_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="BOM 关系已存在")

    bom = BomRelation(
        parent_id=bom_in.parent_id,
        child_id=bom_in.child_id,
        quantity=bom_in.quantity
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return {
        "id": bom.id,
        "parent_id": bom.parent_id,
        "child_id": bom.child_id,
        "quantity": bom.quantity
    }


@router.get("/tree/{part_id}", response_model=BomTreeResponse)
def get_bom_tree(part_id: int, db: Session = Depends(get_db)):
    """递归获取 BOM 树"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="物料不存在")

    tree = build_bom_tree(db, part_id)
    return {
        "part": PartBase(
            id=part.id,
            part_number=part.part_number,
            name=part.name,
            type=part.type,
            spec=part.spec,
            unit=part.unit
        ),
        "tree": tree
    }


@router.put("/{bom_id}")
def update_bom(bom_id: int, bom_in: BomUpdate, db: Session = Depends(get_db)):
    """修改数量"""
    bom = db.query(BomRelation).filter(BomRelation.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 关系不存在")

    bom.quantity = bom_in.quantity
    db.commit()
    db.refresh(bom)
    return {
        "id": bom.id,
        "parent_id": bom.parent_id,
        "child_id": bom.child_id,
        "quantity": bom.quantity
    }


@router.delete("/{bom_id}")
def delete_bom(bom_id: int, db: Session = Depends(get_db)):
    """删除 BOM 关系"""
    bom = db.query(BomRelation).filter(BomRelation.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM 关系不存在")

    db.delete(bom)
    db.commit()
    return {"message": "BOM 关系已删除"}

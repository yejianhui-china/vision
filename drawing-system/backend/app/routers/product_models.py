# ========================================================# 产品型号管理模块# 文件: backend/app/routers/product_models.py# ========================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import ProductModel

router = APIRouter(prefix="/api/product-models", tags=["产品型号管理"])


# ========================================================# Pydantic 数据模型# ========================================================

class ProductModelCreate(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=50, description="产品编码")
    product_name: str = Field(..., min_length=1, max_length=100, description="产品名称")
    spec_model: Optional[str] = Field(None, max_length=200, description="规格型号")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    description: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(True, description="是否启用")


class ProductModelUpdate(BaseModel):
    product_name: Optional[str] = Field(None, max_length=100)
    spec_model: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None)
    is_active: Optional[bool] = None


class ProductModelResponse(BaseModel):
    id: int
    product_code: str
    product_name: str
    spec_model: Optional[str]
    unit: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductModelListResponse(BaseModel):
    total: int
    items: List[ProductModelResponse]


# ========================================================# API# ========================================================

@router.get("", response_model=ProductModelListResponse)
def list_product_models(
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取产品型号列表"""
    query = db.query(ProductModel)

    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (ProductModel.product_code.ilike(search)) |
            (ProductModel.product_name.ilike(search))
        )
    if is_active is not None:
        query = query.filter(ProductModel.is_active == is_active)

    total = query.count()
    items = query.order_by(ProductModel.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.post("", response_model=ProductModelResponse, status_code=status.HTTP_201_CREATED)
def create_product_model(data: ProductModelCreate, db: Session = Depends(get_db)):
    """新建产品型号"""
    if db.query(ProductModel).filter(ProductModel.product_code == data.product_code).first():
        raise HTTPException(status_code=400, detail="产品编码已存在")

    model = ProductModel(**data.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.put("/{model_id}", response_model=ProductModelResponse)
def update_product_model(model_id: int, data: ProductModelUpdate, db: Session = Depends(get_db)):
    """更新产品型号"""
    model = db.query(ProductModel).filter(ProductModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="产品型号不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
def delete_product_model(model_id: int, db: Session = Depends(get_db)):
    """删除产品型号"""
    model = db.query(ProductModel).filter(ProductModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="产品型号不存在")

    db.delete(model)
    db.commit()
    return {"message": "产品型号已删除"}

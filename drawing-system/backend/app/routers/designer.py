# ========================================================
# 销售模块
# 文件: backend/app/routers/designer.py
# 功能: 料号管理、图纸上传、打样申请
# ========================================================

import os
import shutil
from datetime import datetime
from typing import List, Optional

import base64

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Part, Drawing, PrototypeRequest, User
from ..part_number_rules import get_next_part_number, NATURE_CODES, CATEGORY_CODES, SUBCATEGORY_CODES

router = APIRouter(prefix="/api/designer", tags=["销售管理"])

# ========================================================
# 配置
# ========================================================
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========================================================
# Pydantic 模型
# ========================================================

class PartCreate(BaseModel):
    part_number: Optional[str] = Field(None, max_length=50, description="预测单号（自动生成）")
    name: str = Field(..., min_length=1, max_length=100, description="产品名称")
    spec: Optional[str] = Field(None, max_length=200, description="规格型号")
    description: Optional[str] = Field(None, description="备注")
    forecast_period: Optional[str] = Field(None, description="预测周期")
    version: Optional[str] = Field("V1.0", description="版本号")
    customer_region_channel: Optional[str] = Field(None, description="客户/区域/渠道")
    product_code: Optional[str] = Field(None, description="产品编码")
    monthly_forecasts: Optional[list] = Field(None, description="数量时间轴")
    unit: Optional[str] = Field(None, description="单位")
    unit_price: Optional[float] = Field(None, ge=0, description="单价")
    forecast_amount: Optional[float] = Field(None, ge=0, description="预测金额")
    historical_sales: Optional[int] = Field(None, ge=0, description="历史同期销量")
    forecast_basis: Optional[str] = Field(None, description="预测依据")
    approval_status: Optional[str] = Field("draft", description="审批状态")
    nature_code: str = Field(..., min_length=1, max_length=10, description="性质编码")
    category_code: str = Field(..., min_length=1, max_length=10, description="大类编码")
    subcategory_code: str = Field(..., min_length=1, max_length=10, description="小类编码")

class PartUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    spec: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    forecast_period: Optional[str] = Field(None)
    version: Optional[str] = Field(None)
    customer_region_channel: Optional[str] = Field(None)
    product_code: Optional[str] = Field(None)
    monthly_forecasts: Optional[list] = Field(None)
    unit: Optional[str] = Field(None)
    unit_price: Optional[float] = Field(None, ge=0)
    forecast_amount: Optional[float] = Field(None, ge=0)
    historical_sales: Optional[int] = Field(None, ge=0)
    forecast_basis: Optional[str] = Field(None)
    approval_status: Optional[str] = Field(None)
    nature_code: Optional[str] = Field(None, max_length=10)
    category_code: Optional[str] = Field(None, max_length=10)
    subcategory_code: Optional[str] = Field(None, max_length=10)

class PartResponse(BaseModel):
    id: int
    part_number: str
    name: str
    spec: Optional[str]
    description: Optional[str]
    designer_id: int
    status: str
    approval_status: Optional[str]
    extra_data: Optional[dict]
    type: Optional[str]
    nature_code: Optional[str]
    category_code: Optional[str]
    subcategory_code: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PartListResponse(BaseModel):
    total: int
    items: List[PartResponse]

class DrawingResponse(BaseModel):
    id: int
    part_id: int
    file_name: str
    version: str
    uploaded_by: int
    remark: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class PrototypeCreate(BaseModel):
    part_id: int = Field(..., description="关联料号ID")
    quantity: int = Field(default=1, ge=1, description="数量")
    reason: str = Field(..., min_length=1, description="申请原因")

class PrototypeResponse(BaseModel):
    id: int
    part_id: int
    quantity: int
    reason: str
    status: str
    requested_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class PrototypeListResponse(BaseModel):
    total: int
    items: List[PrototypeResponse]

# ========================================================
# 工具函数
# ========================================================

def get_current_user_id(request: Request) -> int:
    """
    从请求头 Authorization 中解析用户 ID
    token 格式: base64(username:id)
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            decoded = base64.b64decode(token).decode("utf-8")
            # 格式: username:id
            user_id = int(decoded.split(":")[-1])
            return user_id
        except Exception:
            pass
    return 1

# ========================================================
# 料号管理 API
# ========================================================

@router.get("/parts", response_model=PartListResponse)
def list_parts(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取料号列表"""
    query = db.query(Part)
    
    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (Part.part_number.ilike(search)) |
            (Part.name.ilike(search))
        )
    if status:
        query = query.filter(Part.status == status)
    
    total = query.count()
    items = query.order_by(Part.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.post("/parts", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(part_in: PartCreate, db: Session = Depends(get_db), request: Request = None):
    """新建销售预测单"""
    # 自动生成料号
    part_number = get_next_part_number(
        db, part_in.nature_code, part_in.category_code, part_in.subcategory_code
    )

    # 检查预测单号是否已存在（兜底）
    if db.query(Part).filter(Part.part_number == part_number).first():
        raise HTTPException(status_code=400, detail="预测单号已存在")

    # 根据大类代码映射物料类型
    TYPE_MAP = {
        "CP": "product",
        "BP": "semi_product",
        "ZJ": "component",
    }
    material_type = TYPE_MAP.get(part_in.category_code, "part")

    extra_data = {
        "forecast_period": part_in.forecast_period,
        "version": part_in.version,
        "customer_region_channel": part_in.customer_region_channel,
        "product_code": part_in.product_code,
        "monthly_forecasts": part_in.monthly_forecasts,
        "unit_price": part_in.unit_price,
        "forecast_amount": part_in.forecast_amount,
        "historical_sales": part_in.historical_sales,
        "forecast_basis": part_in.forecast_basis,
    }
    # 过滤 None 值
    extra_data = {k: v for k, v in extra_data.items() if v is not None}

    part = Part(
        part_number=part_number,
        name=part_in.name,
        spec=part_in.spec,
        description=part_in.description,
        type=material_type,
        unit=part_in.unit,
        designer_id=get_current_user_id(request),
        status="draft",
        approval_status=part_in.approval_status or "draft",
        extra_data=extra_data,
        nature_code=part_in.nature_code,
        category_code=part_in.category_code,
        subcategory_code=part_in.subcategory_code,
    )
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.get("/parts/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    """获取料号详情"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="料号不存在")
    return part


@router.put("/parts/{part_id}", response_model=PartResponse)
def update_part(part_id: int, part_in: PartUpdate, db: Session = Depends(get_db)):
    """更新销售预测单"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="预测单不存在")
    
    update_data = part_in.model_dump(exclude_unset=True)
    
    # 提取扩展字段
    extra_fields = [
        "forecast_period", "version", "customer_region_channel", "product_code",
        "monthly_forecasts",
        "unit", "unit_price", "forecast_amount",
        "historical_sales", "forecast_basis"
    ]
    
    extra = part.extra_data or {}
    for field in extra_fields:
        if field in update_data:
            extra[field] = update_data.pop(field)
    
    part.extra_data = extra
    
    for field, value in update_data.items():
        setattr(part, field, value)
    
    db.commit()
    db.refresh(part)
    return part


@router.delete("/parts/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db)):
    """删除料号"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="料号不存在")
    
    db.delete(part)
    db.commit()
    return {"message": "料号已删除"}


# ========================================================
# 图纸上传 API
# ========================================================

@router.post("/parts/{part_id}/drawings", response_model=DrawingResponse)
def upload_drawing(
    part_id: int,
    file: UploadFile = File(..., description="图纸文件"),
    version: str = Form(default="V1.0", description="版本号"),
    remark: Optional[str] = Form(default=None, description="备注"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """上传图纸到指定料号"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="料号不存在")
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    drawing = Drawing(
        part_id=part_id,
        file_name=file.filename,
        file_path=file_path,
        version=version,
        uploaded_by=get_current_user_id(request),
        remark=remark
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return drawing


@router.get("/parts/{part_id}/drawings", response_model=List[DrawingResponse])
def list_drawings(part_id: int, db: Session = Depends(get_db)):
    """获取料号下的图纸列表"""
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="料号不存在")
    
    drawings = db.query(Drawing).filter(Drawing.part_id == part_id).order_by(Drawing.uploaded_at.desc()).all()
    return drawings


# ========================================================
# 打样申请 API
# ========================================================

@router.post("/prototypes", response_model=PrototypeResponse, status_code=status.HTTP_201_CREATED)
def create_prototype(proto_in: PrototypeCreate, db: Session = Depends(get_db), request: Request = None):
    """发起打样申请"""
    part = db.query(Part).filter(Part.id == proto_in.part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="料号不存在")
    
    proto = PrototypeRequest(
        part_id=proto_in.part_id,
        quantity=proto_in.quantity,
        reason=proto_in.reason,
        status="pending",
        requested_by=get_current_user_id(request)
    )
    db.add(proto)
    db.commit()
    db.refresh(proto)
    return proto


@router.get("/prototypes", response_model=PrototypeListResponse)
def list_prototypes(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取打样申请列表"""
    query = db.query(PrototypeRequest)
    
    if status:
        query = query.filter(PrototypeRequest.status == status)
    
    total = query.count()
    items = query.order_by(PrototypeRequest.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.get("/prototypes/{proto_id}", response_model=PrototypeResponse)
def get_prototype(proto_id: int, db: Session = Depends(get_db)):
    """获取打样申请详情"""
    proto = db.query(PrototypeRequest).filter(PrototypeRequest.id == proto_id).first()
    if not proto:
        raise HTTPException(status_code=404, detail="打样申请不存在")
    return proto


# ========================================================
# 料号编码规则 API
# ========================================================

@router.get("/part-number-rules")
def get_part_number_rules():
    """返回扁平编码规则列表"""
    rules = []
    for nature_code, nature in NATURE_CODES.items():
        for category_code, category in CATEGORY_CODES.items():
            subcategories = SUBCATEGORY_CODES.get(category_code, {})
            for subcategory_code, subcategory in subcategories.items():
                rules.append({
                    "nature_code": nature_code,
                    "nature_name": nature["name"],
                    "category_code": category_code,
                    "category_name": category["name"],
                    "subcategory_code": subcategory_code,
                    "subcategory_name": subcategory["name"],
                })
    return rules


@router.get("/part-number-preview")
def preview_part_number(
    nature_code: str,
    category_code: str,
    subcategory_code: str,
    db: Session = Depends(get_db)
):
    """预览料号"""
    part_number = get_next_part_number(db, nature_code, category_code, subcategory_code)
    return {"preview": part_number}

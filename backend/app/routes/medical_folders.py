"""
病历夹 API 路由

包含：
- 病历夹 CRUD 操作
- 病历夹列表查询

权限控制：用户只能访问自己的病历夹数据
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_folder import MedicalFolder
from ..schemas.medical_folder import (
    MedicalFolderCreate, MedicalFolderUpdate, MedicalFolderResponse,
    MedicalFolderListResponse
)

router = APIRouter(prefix="/medical-folders", tags=["medical-folders"])
logger = logging.getLogger(__name__)


# ============= 权限检查辅助函数 =============

def get_folder_with_permission(
    folder_id: str,
    user: User,
    db: Session
) -> MedicalFolder:
    """获取病历夹并验证权限"""
    import uuid
    try:
        folder_id_uuid = uuid.UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件夹ID")

    folder = db.query(MedicalFolder).filter(MedicalFolder.id == folder_id_uuid).first()

    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历夹不存在")

    if folder.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此病历夹")

    return folder


# ============= 病历夹 CRUD =============

@router.post("", response_model=MedicalFolderResponse, status_code=status.HTTP_201_CREATED)
def create_medical_folder(
    request: MedicalFolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建病历夹

    用户可以创建自定义文件夹来组织病历记录
    """
    # 检查同名文件夹
    existing = db.query(MedicalFolder).filter(
        MedicalFolder.user_id == current_user.id,
        MedicalFolder.name == request.name
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已存在同名文件夹")

    folder = MedicalFolder(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        color=request.color,
        icon=request.icon,
        sort_order=request.sort_order
    )

    db.add(folder)
    db.commit()
    db.refresh(folder)

    logger.info(f"Created medical folder {folder.id} for user {current_user.id}")
    return MedicalFolderResponse(
        id=str(folder.id),
        user_id=folder.user_id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        icon=folder.icon,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        record_count=0
    )


@router.get("", response_model=MedicalFolderListResponse)
def list_medical_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的所有病历夹

    按 sort_order 排序
    """
    folders = db.query(MedicalFolder).filter(
        MedicalFolder.user_id == current_user.id
    ).order_by(MedicalFolder.sort_order, MedicalFolder.created_at).all()

    # 获取每个文件夹的记录数量
    result = []
    for folder in folders:
        record_count = len(folder.records) if folder.records else 0
        result.append(MedicalFolderResponse(
            id=str(folder.id),
            user_id=folder.user_id,
            name=folder.name,
            description=folder.description,
            color=folder.color,
            icon=folder.icon,
            sort_order=folder.sort_order,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            record_count=record_count
        ))

    return MedicalFolderListResponse(folders=result, total=len(result))


@router.get("/{folder_id}", response_model=MedicalFolderResponse)
def get_medical_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取病历夹详情"""
    folder = get_folder_with_permission(folder_id, current_user, db)
    record_count = len(folder.records) if folder.records else 0

    return MedicalFolderResponse(
        id=str(folder.id),
        user_id=folder.user_id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        icon=folder.icon,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        record_count=record_count
    )


@router.put("/{folder_id}", response_model=MedicalFolderResponse)
def update_medical_folder(
    folder_id: str,
    request: MedicalFolderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新病历夹"""
    folder = get_folder_with_permission(folder_id, current_user, db)

    # 检查同名文件夹（排除当前文件夹）
    if request.name is not None:
        existing = db.query(MedicalFolder).filter(
            MedicalFolder.user_id == current_user.id,
            MedicalFolder.name == request.name,
            MedicalFolder.id != folder.id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已存在同名文件夹")

    # 更新字段
    if request.name is not None:
        folder.name = request.name
    if request.description is not None:
        folder.description = request.description
    if request.color is not None:
        folder.color = request.color
    if request.icon is not None:
        folder.icon = request.icon
    if request.sort_order is not None:
        folder.sort_order = request.sort_order

    db.commit()
    db.refresh(folder)

    record_count = len(folder.records) if folder.records else 0
    logger.info(f"Updated medical folder {folder.id} for user {current_user.id}")

    return MedicalFolderResponse(
        id=str(folder.id),
        user_id=folder.user_id,
        name=folder.name,
        description=folder.description,
        color=folder.color,
        icon=folder.icon,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        record_count=record_count
    )


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medical_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除病历夹

    注意：这将级联删除该文件夹下的所有病历记录和文件
    """
    folder = get_folder_with_permission(folder_id, current_user, db)

    # 检查文件夹是否为空（可选，根据需求决定是否强制）
    record_count = len(folder.records) if folder.records else 0
    if record_count > 0:
        # 可以选择禁止删除非空文件夹，或者允许但给出警告
        logger.warning(f"Deleting non-empty folder {folder.id} with {record_count} records")

    db.delete(folder)
    db.commit()

    logger.info(f"Deleted medical folder {folder.id} for user {current_user.id}")
    return None

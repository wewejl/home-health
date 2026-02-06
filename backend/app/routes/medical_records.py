"""
病历记录 API 路由

包含：
- 病历记录 CRUD 操作
- 按文件夹查询病历记录

权限控制：用户只能访问自己的病历记录数据
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_record import MedicalRecord
from ..models.medical_folder import MedicalFolder
from ..schemas.medical_record import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse,
    MedicalRecordDetailResponse, MedicalRecordListResponse
)

router = APIRouter(prefix="/medical-records", tags=["medical-records"])
logger = logging.getLogger(__name__)


# ============= 权限检查辅助函数 =============

def get_record_with_permission(
    record_id: str,
    user: User,
    db: Session
) -> MedicalRecord:
    """获取病历记录并验证权限"""
    import uuid
    try:
        record_id_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的记录ID")

    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id_uuid).first()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历记录不存在")

    if record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此病历记录")

    return record


def verify_folder_access(
    folder_id: str,
    user: User,
    db: Session
) -> MedicalFolder:
    """验证文件夹是否属于当前用户"""
    import uuid
    try:
        folder_id_uuid = uuid.UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件夹ID")

    folder = db.query(MedicalFolder).filter(MedicalFolder.id == folder_id_uuid).first()

    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")

    if folder.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此文件夹")

    return folder


# ============= 病历记录 CRUD =============

@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    request: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建病历记录

    用户在指定文件夹下创建新的病历记录
    """
    # 验证文件夹权限
    folder = verify_folder_access(request.folder_id, current_user, db)

    record = MedicalRecord(
        folder_id=request.folder_id,
        user_id=current_user.id,
        title=request.title,
        record_date=request.record_date,
        description=request.description
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(f"Created medical record {record.id} for user {current_user.id} in folder {folder.id}")
    return MedicalRecordResponse(
        id=str(record.id),
        folder_id=str(record.folder_id),
        user_id=record.user_id,
        title=record.title,
        record_date=record.record_date,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        file_count=0
    )


@router.get("", response_model=MedicalRecordListResponse)
def list_medical_records(
    folder_id: Optional[str] = Query(None, description="筛选指定文件夹下的记录"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取病历记录列表

    可按文件夹筛选，默认返回所有记录
    """
    query = db.query(MedicalRecord).filter(MedicalRecord.user_id == current_user.id)

    if folder_id:
        import uuid
        try:
            folder_id_uuid = uuid.UUID(folder_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件夹ID")
        query = query.filter(MedicalRecord.folder_id == folder_id_uuid)

    records = query.order_by(MedicalRecord.record_date.desc(), MedicalRecord.created_at.desc()).all()

    result = []
    for record in records:
        file_count = len(record.files) if record.files else 0
        result.append(MedicalRecordResponse(
            id=str(record.id),
            folder_id=str(record.folder_id),
            user_id=record.user_id,
            title=record.title,
            record_date=record.record_date,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
            file_count=file_count
        ))

    return MedicalRecordListResponse(records=result, total=len(result))


@router.get("/{record_id}", response_model=MedicalRecordDetailResponse)
def get_medical_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取病历记录详情（包含文件列表）"""
    record = get_record_with_permission(record_id, current_user, db)

    files = []
    if record.files:
        from ..schemas.medical_file import MedicalFileResponse
        for file in record.files:
            files.append(MedicalFileResponse(
                id=str(file.id),
                record_id=str(file.record_id),
                user_id=file.user_id,
                filename=file.filename,
                file_type=file.file_type,
                mime_type=file.mime_type,
                file_size=file.file_size,
                url=file.url,
                thumbnail_url=file.thumbnail_url,
                created_at=file.created_at,
                updated_at=file.updated_at
            ))

    return MedicalRecordDetailResponse(
        id=str(record.id),
        folder_id=str(record.folder_id),
        user_id=record.user_id,
        title=record.title,
        record_date=record.record_date,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        file_count=len(files),
        files=files
    )


@router.put("/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    record_id: str,
    request: MedicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新病历记录"""
    record = get_record_with_permission(record_id, current_user, db)

    # 如果要修改文件夹，验证新文件夹权限
    if request.folder_id is not None:
        verify_folder_access(request.folder_id, current_user, db)
        record.folder_id = request.folder_id

    if request.title is not None:
        record.title = request.title
    if request.record_date is not None:
        record.record_date = request.record_date
    if request.description is not None:
        record.description = request.description

    db.commit()
    db.refresh(record)

    file_count = len(record.files) if record.files else 0
    logger.info(f"Updated medical record {record.id} for user {current_user.id}")

    return MedicalRecordResponse(
        id=str(record.id),
        folder_id=str(record.folder_id),
        user_id=record.user_id,
        title=record.title,
        record_date=record.record_date,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        file_count=file_count
    )


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medical_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除病历记录

    注意：这将级联删除该记录下的所有文件
    """
    record = get_record_with_permission(record_id, current_user, db)

    # 记录文件数量用于日志
    file_count = len(record.files) if record.files else 0
    if file_count > 0:
        logger.warning(f"Deleting record {record.id} with {file_count} files")

    db.delete(record)
    db.commit()

    logger.info(f"Deleted medical record {record.id} for user {current_user.id}")
    return None


@router.get("/by-folder/{folder_id}", response_model=MedicalRecordListResponse)
def get_records_by_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定文件夹下的所有病历记录
    """
    # 验证文件夹权限
    verify_folder_access(folder_id, current_user, db)

    import uuid
    try:
        folder_id_uuid = uuid.UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件夹ID")

    records = db.query(MedicalRecord).filter(
        MedicalRecord.user_id == current_user.id,
        MedicalRecord.folder_id == folder_id_uuid
    ).order_by(MedicalRecord.record_date.desc(), MedicalRecord.created_at.desc()).all()

    result = []
    for record in records:
        file_count = len(record.files) if record.files else 0
        result.append(MedicalRecordResponse(
            id=str(record.id),
            folder_id=str(record.folder_id),
            user_id=record.user_id,
            title=record.title,
            record_date=record.record_date,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
            file_count=file_count
        ))

    return MedicalRecordListResponse(records=result, total=len(result))

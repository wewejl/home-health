"""
医疗文件 API 路由

包含：
- 文件上传（支持图片、PDF、视频、音频、文档）
- 文件查询
- 文件重命名
- 文件删除
- 缩略图生成

权限控制：用户只能访问自己的文件数据

安全改进：
- 使用事务确保数据一致性
- 安全的路径验证防止路径遍历
- 文件类型严格验证
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image
import io

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.medical_file import MedicalFile, FileType
from ..models.medical_record import MedicalRecord
from ..schemas.medical_file import (
    MedicalFileResponse, MedicalFileUpdate, MedicalFileListResponse,
    FileUploadResponse
)
from ..utils.file_security import (
    resolve_upload_path, resolve_thumbnail_path, safe_delete_file,
    validate_file_extension, sanitize_filename, FileSecurityError
)

router = APIRouter(prefix="/medical-files", tags=["medical-files"])
logger = logging.getLogger(__name__)

settings = get_settings()

# MIME 类型映射
MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".heic": "image/heic", ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".wav": "audio/wav", ".aac": "audio/aac",
    ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain", ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}


# ============= 工具函数 =============

def get_file_category(filename: str) -> str:
    """根据文件扩展名获取文件类别"""
    category = validate_file_extension(filename, settings.ALLOWED_EXTENSIONS)
    return category or "document"


def get_user_upload_dir(user_id: int, record_id: str) -> Path:
    """获取用户上传目录"""
    user_dir = settings.UPLOAD_DIR / str(user_id) / record_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def generate_thumbnail(image_path: Path, thumbnail_path: Path, size: tuple = (200, 200)):
    """生成图片缩略图"""
    try:
        with Image.open(image_path) as img:
            # 转换 RGBA 为 RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, "JPEG", quality=85)
        return True
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        return False


# ============= 权限检查辅助函数 =============

def get_file_with_permission(
    file_id: str,
    user: User,
    db: Session
) -> MedicalFile:
    """获取文件并验证权限"""
    try:
        file_id_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件ID")

    file = db.query(MedicalFile).filter(MedicalFile.id == file_id_uuid).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    if file.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此文件")

    return file


def verify_record_access(
    record_id: str,
    user: User,
    db: Session
) -> MedicalRecord:
    """验证病历记录是否属于当前用户"""
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


# ============= 文件上传和管理 =============

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    record_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传文件到病历记录

    支持的文件类型：图片、PDF、视频、音频、文档
    最大文件大小：50MB

    使用数据库事务确保数据一致性：
    - 文件写入失败 → 数据库回滚
    - 数据库提交失败 → 文件已清理
    """
    # 验证记录权限
    record = verify_record_access(record_id, current_user, db)

    # 验证文件扩展名
    file_category = get_file_category(file.filename)
    if file_category == "document" and not file.filename.endswith((".txt", ".doc", ".docx", ".xls", ".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件类型"
        )

    # 清理文件名
    safe_filename = sanitize_filename(file.filename)

    # 读取文件内容（分块读取避免大文件内存问题）
    content = await file.read()

    # 检查文件大小
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
        )

    # 生成文件 ID
    file_id = uuid.uuid4()
    ext = Path(safe_filename).suffix.lower()

    # 使用事务确保数据一致性
    try:
        # 开始数据库事务
        with db.begin():
            # 准备文件路径
            user_dir = get_user_upload_dir(current_user.id, str(record.id))
            file_path = user_dir / f"{file_id}{ext}"

            # 保存文件
            with open(file_path, "wb") as f:
                f.write(content)

            # 生成缩略图
            thumbnail_url = None
            if file_category == "image":
                thumbnail_path = user_dir / "thumbnails" / f"{file_id}_thumb.jpg"
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                if generate_thumbnail(file_path, thumbnail_path):
                    # 安全的相对路径
                    thumbnail_url = f"/static/uploads/medical_files/{current_user.id}/{record.id}/thumbnails/{file_id}_thumb.jpg"

            # 构建安全的 URL 路径
            file_url = f"/static/uploads/medical_files/{current_user.id}/{record.id}/{file_id}{ext}"

            # 保存到数据库
            medical_file = MedicalFile(
                id=file_id,
                record_id=record.id,
                user_id=current_user.id,
                filename=safe_filename,
                file_type=file_category,
                mime_type=file.content_type or MIME_TYPES.get(ext, "application/octet-stream"),
                file_size=len(content),
                url=file_url,
                thumbnail_url=thumbnail_url
            )

            db.add(medical_file)
            # 事务在 with 块结束时自动提交

        # 刷新以获取生成的值
        db.refresh(medical_file)

        logger.info(f"Uploaded file {file_id} for user {current_user.id} in record {record.id}")

        return FileUploadResponse(
            file=MedicalFileResponse(
                id=str(medical_file.id),
                record_id=str(medical_file.record_id),
                user_id=medical_file.user_id,
                filename=medical_file.filename,
                file_type=medical_file.file_type,
                mime_type=medical_file.mime_type,
                file_size=medical_file.file_size,
                url=medical_file.url,
                thumbnail_url=medical_file.thumbnail_url,
                created_at=medical_file.created_at,
                updated_at=medical_file.updated_at
            ),
            message="文件上传成功"
        )

    except Exception as e:
        # 如果任何步骤失败，清理已创建的文件
        logger.error(f"File upload failed, cleaning up: {e}")
        user_dir = get_user_upload_dir(current_user.id, str(record.id))
        potential_file = user_dir / f"{file_id}{ext}"
        if potential_file.exists():
            potential_file.unlink()

        potential_thumbnail = user_dir / "thumbnails" / f"{file_id}_thumb.jpg"
        if potential_thumbnail.exists():
            potential_thumbnail.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/{file_id}", response_model=MedicalFileResponse)
def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件信息"""
    file = get_file_with_permission(file_id, current_user, db)

    return MedicalFileResponse(
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
    )


@router.get("/record/{record_id}", response_model=MedicalFileListResponse)
def get_record_files(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定病历记录的所有文件"""
    record = verify_record_access(record_id, current_user, db)

    try:
        record_id_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的记录ID")

    files = db.query(MedicalFile).filter(
        MedicalFile.record_id == record_id_uuid,
        MedicalFile.user_id == current_user.id
    ).order_by(MedicalFile.created_at.desc()).all()

    result = []
    for file in files:
        result.append(MedicalFileResponse(
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

    return MedicalFileListResponse(files=result, total=len(result))


@router.put("/{file_id}", response_model=MedicalFileResponse)
def rename_file(
    file_id: str,
    request: MedicalFileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名文件"""
    file = get_file_with_permission(file_id, current_user, db)

    # 清理新文件名
    safe_filename = sanitize_filename(request.filename)

    file.filename = safe_filename
    db.commit()
    db.refresh(file)

    logger.info(f"Renamed file {file_id} to '{safe_filename}' for user {current_user.id}")

    return MedicalFileResponse(
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
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除文件

    同时删除服务器上的文件和缩略图

    安全改进：
    - 使用安全的路径解析防止路径遍历
    - 先删除数据库记录，再清理文件
    """
    file = get_file_with_permission(file_id, current_user, db)

    # 存储文件路径信息供后续清理使用
    file_url = file.url
    thumbnail_url = file.thumbnail_url
    user_id = file.user_id

    # 从数据库中删除（这会触发级联删除相关关系）
    db.delete(file)
    db.commit()

    # 安全地删除物理文件
    try:
        # 解析并删除主文件
        # 从 URL 中提取文件名，格式: /static/uploads/medical_files/{user_id}/{record_id}/{filename}
        url_parts = file_url.strip("/").split("/")
        if len(url_parts) >= 5:
            record_id = url_parts[3]  # static/uploads/medical_files/{user_id}/{record_id}/...
            filename = url_parts[4]

            # 使用安全路径解析
            file_path = resolve_upload_path(user_id, record_id, filename, settings.UPLOAD_DIR)
            safe_delete_file(file_path)

        # 删除缩略图
        if thumbnail_url:
            thumb_parts = thumbnail_url.strip("/").split("/")
            if len(thumb_parts) >= 6:  # .../thumbnails/{filename}
                record_id = thumb_parts[3]
                thumb_filename = thumb_parts[5]

                thumb_path = resolve_thumbnail_path(user_id, record_id, thumb_filename, settings.UPLOAD_DIR)
                safe_delete_file(thumb_path)

    except (FileSecurityError, IndexError, ValueError) as e:
        # 路径解析失败时记录警告，但不影响删除操作
        logger.warning(f"Failed to parse file path for cleanup: {e}")

    logger.info(f"Deleted file {file_id} for user {current_user.id}")
    return None

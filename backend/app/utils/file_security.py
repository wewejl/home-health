"""
文件安全工具模块

提供安全的文件路径验证和操作，防止路径遍历攻击
"""
from pathlib import Path
from typing import Optional
import re


class FileSecurityError(Exception):
    """文件安全相关异常"""
    pass


def resolve_upload_path(user_id: int, record_id: str, filename: str, base_dir: Path) -> Path:
    """
    解析安全的上传文件路径

    Args:
        user_id: 用户 ID
        record_id: 记录 ID (应该是 UUID 格式)
        filename: 文件名
        base_dir: 基础上传目录

    Returns:
        安全的绝对路径

    Raises:
        FileSecurityError: 如果路径不安全
    """
    # 验证 record_id 是否为有效的 UUID 格式（防止路径遍历）
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    if not uuid_pattern.match(record_id):
        raise FileSecurityError(f"Invalid record_id format: {record_id}")

    # 验证用户 ID 是数字
    if not isinstance(user_id, int) or user_id <= 0:
        raise FileSecurityError(f"Invalid user_id: {user_id}")

    # 清理文件名，移除路径分隔符和特殊字符
    safe_filename = Path(filename).name
    if not safe_filename or safe_filename in (".", ".."):
        raise FileSecurityError(f"Invalid filename: {filename}")

    # 构建路径并解析为绝对路径
    full_path = (base_dir / str(user_id) / record_id / safe_filename).resolve()

    # 确保解析后的路径仍然在基础目录内
    base_dir_resolved = base_dir.resolve()
    try:
        full_path.relative_to(base_dir_resolved)
    except ValueError:
        raise FileSecurityError(f"Path traversal attempt detected: {full_path}")

    return full_path


def resolve_thumbnail_path(user_id: int, record_id: str, filename: str, base_dir: Path) -> Path:
    """
    解析安全的缩略图路径

    Args:
        user_id: 用户 ID
        record_id: 记录 ID
        filename: 缩略图文件名
        base_dir: 基础上传目录

    Returns:
        安全的缩略图绝对路径
    """
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    if not uuid_pattern.match(record_id):
        raise FileSecurityError(f"Invalid record_id format: {record_id}")

    safe_filename = Path(filename).name
    if not safe_filename or safe_filename in (".", ".."):
        raise FileSecurityError(f"Invalid filename: {filename}")

    full_path = (base_dir / str(user_id) / record_id / "thumbnails" / safe_filename).resolve()

    base_dir_resolved = base_dir.resolve()
    try:
        full_path.relative_to(base_dir_resolved)
    except ValueError:
        raise FileSecurityError(f"Path traversal attempt detected: {full_path}")

    return full_path


def safe_delete_file(file_path: Path) -> bool:
    """
    安全删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功删除
    """
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False


def validate_file_extension(filename: str, allowed_extensions: dict) -> Optional[str]:
    """
    验证文件扩展名是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名字典

    Returns:
        文件类别，如果不允许则返回 None
    """
    ext = Path(filename).suffix.lower()
    for category, extensions in allowed_extensions.items():
        if ext in extensions:
            return category
    return None


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 只保留文件名部分，移除路径
    name = Path(filename).name

    # 替换危险字符
    name = re.sub(r'[<>:"/\\|?*]', '_', name)

    # 限制文件名长度
    if len(name) > 255:
        name = name[:255]

    return name if name else "unnamed"

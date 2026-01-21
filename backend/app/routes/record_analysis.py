"""
病历分析 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ..database import get_db
from ..models.doctor import Doctor
from ..models.admin_user import AdminUser, AuditLog
from ..services.record_analysis_service import RecordAnalysisService
from ..services.qwen_service import QwenService
from .admin_auth import get_current_admin


router = APIRouter(prefix="/admin/doctors", tags=["admin-record-analysis"])


@router.post("/{doctor_id}/analyze-records")
async def analyze_medical_records(
    doctor_id: int,
    files: List[UploadFile] = File(..., description="病历文件（PDF/图片/TXT）"),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    上传病历文件，AI 分析提取诊疗特征

    流程：
    1. 解析上传文件（PDF 提取文字，图片调用 OCR）
    2. 提取诊疗特征（诊断思路、用药规律、随访习惯）
    3. 生成 ai_persona_prompt
    4. 返回分析结果供确认
    """
    # 验证医生存在
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    # 验证文件数量和大小
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最多支持上传 5 个文件")

    # 读取文件内容
    file_data = []
    total_size = 0
    for file in files:
        content = await file.read()
        total_size += len(content)

        # 单文件大小限制 10MB
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"文件 {file.filename} 超过 10MB 限制"
            )

        # 验证文件格式
        if not file.filename:
            continue

        ext = file.filename.lower().split('.')[-1]
        if ext not in ['pdf', 'jpg', 'jpeg', 'png', 'webp', 'txt']:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {ext}"
            )

        file_data.append((file.filename, content))

    # 总大小限制 50MB
    if total_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件总大小超过 50MB 限制")

    try:
        # 调用分析服务
        result = await RecordAnalysisService.analyze_records(
            files=file_data,
            qwen_service=QwenService
        )

        # 记录审计日志
        log = AuditLog(
            admin_user_id=admin.id,
            action="analyze_records",
            resource_type="doctor",
            resource_id=str(doctor_id),
            changes={
                "files_count": len(files),
                "text_length": result["total_text_length"]
            }
        )
        db.add(log)
        db.commit()

        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor.name,
            "parsed_files": result["parsed_files"],
            "features": result["features"],
            "generated_prompt": result["generated_prompt"],
            "preview_length": result["total_text_length"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/{doctor_id}/save-analysis")
async def save_analysis_result(
    doctor_id: int,
    ai_persona_prompt: str = Form(..., description="生成的 AI 人设 Prompt"),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    保存病历分析结果到医生配置

    更新 ai_persona_prompt 和 records_analyzed 标记
    """
    # 验证医生存在
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    # 更新医生配置
    doctor.ai_persona_prompt = ai_persona_prompt
    if hasattr(doctor, 'records_analyzed'):
        doctor.records_analyzed = True

    # 记录审计日志
    log = AuditLog(
        admin_user_id=admin.id,
        action="save_analysis",
        resource_type="doctor",
        resource_id=str(doctor_id),
        changes={"prompt_length": len(ai_persona_prompt)}
    )
    db.add(log)
    db.commit()

    return {
        "message": "病历分析结果已保存",
        "doctor_id": doctor_id,
        "prompt_length": len(ai_persona_prompt)
    }


@router.get("/{doctor_id}/analysis-status")
async def get_analysis_status(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    获取医生病历分析状态
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")

    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor.name,
        "records_analyzed": getattr(doctor, 'records_analyzed', False),
        "has_persona_prompt": bool(doctor.ai_persona_prompt),
        "prompt_length": len(doctor.ai_persona_prompt) if doctor.ai_persona_prompt else 0
    }

"""
智能问诊记录工具
"""
import json
from datetime import datetime
from pathlib import Path


MEDICAL_RECORDS_DIR = Path("data/medical_records")


def save_to_his_system(
    patient_id: str,
    his_user_id: str,
    main_symptom: str,
    accompanying_symptoms: str = "",
    medical_history: str = "",
    lifestyle: str = ""
) -> str:
    """保存结构化病历到本地 JSON 文件

    Args:
        patient_id: 患者 ID
        his_user_id: 医生 ID
        main_symptom: 主要症状描述
        accompanying_symptoms: 伴随症状描述
        medical_history: 既往史描述
        lifestyle: 生活习惯描述

    Returns:
        str: 病历编号，例如 "MR20250301153045"
    """
    # 生成病历编号
    record_id = f"MR{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 构造数据
    data = {
        "record_id": record_id,
        "patient_id": patient_id,
        "his_user_id": his_user_id,
        "created_at": datetime.now().isoformat(),
        "main_symptom": {"description": main_symptom},
        "accompanying_symptoms": {"description": accompanying_symptoms},
        "medical_history": {"description": medical_history},
        "lifestyle": {"description": lifestyle}
    }

    # 按患者分目录存储
    patient_dir = MEDICAL_RECORDS_DIR / patient_id
    patient_dir.mkdir(parents=True, exist_ok=True)

    # 保存文件
    file_path = patient_dir / f"{record_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 返回病历完整信息（供主Agent生成总结）
    info = f"工具执行成功。病历编号：{record_id}。"
    info += f"患者ID：{patient_id}。"
    info += f"主诉：{main_symptom}。"

    if accompanying_symptoms:
        info += f"伴随症状：{accompanying_symptoms}。"
    if medical_history:
        info += f"既往病史：{medical_history}。"
    if lifestyle:
        info += f"生活习惯：{lifestyle}。"

    info += f"请根据以上病历信息生成完整的总结和医疗建议。"

    return info

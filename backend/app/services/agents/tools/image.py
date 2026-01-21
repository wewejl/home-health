"""
皮肤图像分析工具

调用视觉模型分析皮肤照片
"""
from typing import Dict, Any

# 工具 Schema
IMAGE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_skin_image",
        "description": "分析皮肤图像，识别皮肤病变特征。当患者上传了皮肤照片时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "image_base64": {
                    "type": "string",
                    "description": "Base64 编码的图片数据"
                },
                "context": {
                    "type": "string",
                    "description": "患者提供的上下文信息，如主诉、症状描述等"
                }
            },
            "required": ["image_base64"]
        }
    }
}


async def analyze_skin_image(
    image_base64: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    分析皮肤图像
    
    Args:
        image_base64: Base64 编码的图片
        context: 上下文信息
        
    Returns:
        {
            "success": True/False,
            "findings": "图像分析发现",
            "possible_conditions": [...],
            "confidence": 0-1,
            "recommendations": [...]
        }
    """
    # 导入视觉服务（延迟导入避免循环依赖）
    from ...qwen_vl_service import qwen_vl_service
    
    if not image_base64:
        return {
            "success": False,
            "findings": "",
            "possible_conditions": [],
            "error": "未提供图片数据"
        }
    
    try:
        # 调用 qwen-vl 服务分析图片
        analysis_result = await qwen_vl_service.analyze_skin_image(
            image_base64=image_base64,
            context=context
        )
        
        # 解析分析结果
        return {
            "success": True,
            "findings": analysis_result,
            "possible_conditions": _extract_conditions(analysis_result),
            "confidence": 0.7,  # 默认置信度
            "recommendations": [
                "图像分析仅供参考，不能替代医生诊断",
                "如有疑虑，建议线下就医检查"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "findings": "",
            "possible_conditions": [],
            "error": f"图像分析失败: {str(e)}"
        }


def _extract_conditions(analysis_text: str) -> list:
    """
    从分析文本中提取可能的疾病
    """
    conditions = []
    
    # 常见皮肤病关键词
    condition_keywords = [
        "湿疹", "皮炎", "银屑病", "牛皮癣", "荨麻疹",
        "痤疮", "粉刺", "疱疹", "真菌感染", "癣",
        "过敏", "红斑", "丘疹", "水疱", "脓疱"
    ]
    
    for keyword in condition_keywords:
        if keyword in analysis_text:
            conditions.append(keyword)
    
    return conditions[:5]  # 最多返回5个

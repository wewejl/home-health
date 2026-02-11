"""
AI 分身聊天 API 测试

测试覆盖：
- persona_chat.py: 医生分身对话式采集 API
- record_analysis.py: 医疗记录分析 API
- Mock AI 服务调用（不实际调用 LLM）
- 验证请求和响应格式
- 测试错误处理
"""
import pytest
import os
import json
from io import BytesIO
from unittest.mock import AsyncMock, patch, MagicMock

# 设置测试模式
os.environ["TEST_MODE"] = "true"


class TestStartPersonaCollection:
    """测试开始医生分身对话式采集"""

    def test_start_collection_success(self, test_client, db_session):
        """测试成功开始采集流程"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        # 创建科室
        department = Department(name="心内科", description="心血管内科")
        db_session.add(department)
        db_session.flush()

        # 创建医生
        doctor = Doctor(
            name="张医生",
            specialty="心血管内科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat/start"
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "state" in data
        assert "stage" in data
        assert data["stage"] == "greeting"
        assert data["is_complete"] is False
        assert "您好" in data["message"] or "医生分身" in data["message"]

    def test_start_collection_nonexistent_doctor(self, test_client):
        """测试不存在的医生 ID"""
        response = test_client.post("/admin/doctors/99999/persona-chat/start")
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data.get("detail", "")

    def test_start_collection_without_specialty(self, test_client, db_session):
        """测试没有专科信息的医生"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="全科", description="全科医学科")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="李医生",
            specialty=None,  # 无专科信息
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat/start"
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # 应该使用默认专科"全科医学"


class TestPersonaChatMessage:
    """测试对话式采集消息处理"""

    def test_send_first_message(self, test_client, db_session):
        """测试发送第一条消息（从 greeting 进入 specialty）"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="神经内科", description="神经内科")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="王医生",
            specialty="神经内科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 首先开始采集
        start_response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat/start"
        )
        start_data = start_response.json()
        initial_state = start_data["state"]

        # 发送第一条消息
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={
                "message": "准备好了",
                "state": initial_state
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "state" in data
        assert "stage" in data
        assert data["stage"] == "specialty"
        assert data["is_complete"] is False

    def test_send_message_without_state(self, test_client, db_session):
        """测试不提供状态的消息"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="儿科", description="儿科")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="赵医生",
            specialty="儿科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={
                "message": "测试",
                "state": None
            }
        )

        assert response.status_code == 200
        # 应该从初始状态开始处理

    def test_send_message_with_invalid_state_json(self, test_client, db_session):
        """测试状态 JSON 格式错误"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="骨科", description="骨科")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="孙医生",
            specialty="骨科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={
                "message": "测试",
                "state": "invalid json{{"
            }
        )

        assert response.status_code == 200
        # 应该重置为初始状态

    def test_send_message_nonexistent_doctor(self, test_client):
        """测试向不存在的医生发送消息"""
        response = test_client.post(
            "/admin/doctors/99999/persona-chat",
            json={
                "message": "测试",
                "state": "{}"
            }
        )
        assert response.status_code == 404


class TestPersonaChatCompleteFlow:
    """测试完整的对话采集流程"""

    def test_complete_collection_flow(self, test_client, db_session):
        """测试完整的采集流程到完成"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="测试医生",
            specialty="测试专科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 开始
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat/start"
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "greeting"

        # 1. greeting -> specialty
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "开始", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "specialty"

        # 2. specialty -> style
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "我关注患者的精神状态和食欲", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "style"

        # 3. style -> approach
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "我说话温和，用通俗语言", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "approach"

        # 4. approach -> prescription
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "先听患者说完，然后追问", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "prescription"

        # 5. prescription -> advice
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "保守治疗，单一用药", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "advice"

        # 6. advice -> summary
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "建议三分治七分养", "state": state}
        )
        data = response.json()
        state = data["state"]
        assert data["stage"] == "summary"

        # 7. summary -> complete (确认)
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "确认", "state": state}
        )
        data = response.json()
        assert data["is_complete"] is True
        assert "generated_prompt" in data
        assert data["generated_prompt"] is not None
        assert len(data["generated_prompt"]) > 0

        # 验证医生记录已更新
        db_session.refresh(doctor)
        assert doctor.ai_persona_prompt is not None
        assert doctor.ai_persona_prompt == data["generated_prompt"]

    def test_summary_modify_stage(self, test_client, db_session):
        """测试总结阶段修改某个阶段"""
        from app.models.doctor import Doctor
        from app.models.department import Department
        from app.services.persona_collection_service import CollectionState, CollectionStage

        department = Department(name="测试科室2", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="测试医生2",
            specialty="测试专科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建到 summary 阶段的状态
        state = CollectionState()
        state.stage = CollectionStage.SUMMARY
        state.specialty_focus = "儿科关注点"
        state.communication_style = "温和"
        state.inquiry_approach = "系统问诊"
        state.prescription_preferences = "保守"
        state.advice_template = "规律作息"

        state_json = json.dumps(state.to_dict(), ensure_ascii=False)

        # 请求修改
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "修改专科", "state": state_json}
        )
        data = response.json()
        assert data["stage"] == "specialty"
        assert "修改" in data["message"]

    def test_summary_restart(self, test_client, db_session):
        """测试总结阶段重新开始"""
        from app.models.doctor import Doctor
        from app.models.department import Department
        from app.services.persona_collection_service import CollectionState, CollectionStage

        department = Department(name="测试科室3", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="测试医生3",
            specialty="测试专科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建到 summary 阶段的状态
        state = CollectionState()
        state.stage = CollectionStage.SUMMARY
        state.specialty_focus = "已填写"

        state_json = json.dumps(state.to_dict(), ensure_ascii=False)

        # 重新开始
        response = test_client.post(
            f"/admin/doctors/{doctor.id}/persona-chat",
            json={"message": "重新开始", "state": state_json}
        )
        data = response.json()
        assert data["stage"] == "greeting"
        assert "重新开始" in data["message"]


class TestGetPersonaStatus:
    """测试获取医生分身配置状态"""

    def test_get_status_existing_doctor(self, test_client, db_session):
        """测试获取存在的医生状态"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="状态医生",
            specialty="测试专科",
            ai_model="qwen-plus",
            ai_temperature=0.8,
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.get(f"/admin/doctors/{doctor.id}/persona-status")

        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == doctor.id
        assert data["name"] == "状态医生"
        assert "persona_completed" in data
        assert "has_persona_prompt" in data
        assert "ai_model" in data
        assert "ai_temperature" in data

    def test_get_status_with_prompt(self, test_client, db_session):
        """测试已有 prompt 的医生状态"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="有Prompt医生",
            specialty="测试专科",
            ai_persona_prompt="这是一个测试提示词",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.get(f"/admin/doctors/{doctor.id}/persona-status")

        assert response.status_code == 200
        data = response.json()
        assert data["has_persona_prompt"] is True

    def test_get_status_nonexistent_doctor(self, test_client):
        """测试获取不存在医生的状态"""
        response = test_client.get("/admin/doctors/99999/persona-status")
        assert response.status_code == 404


class TestResetPersonaCollection:
    """测试重置医生分身采集状态"""

    def test_reset_success(self, test_client, db_session):
        """测试成功重置"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="重置医生",
            specialty="测试专科",
            ai_persona_prompt="旧的提示词",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.post(f"/admin/doctors/{doctor.id}/persona-chat/reset")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "重置" in data["message"]
        assert data["doctor_id"] == doctor.id

        # 验证数据库已更新
        db_session.refresh(doctor)
        assert doctor.ai_persona_prompt is None

    def test_reset_nonexistent_doctor(self, test_client):
        """测试重置不存在的医生"""
        response = test_client.post("/admin/doctors/99999/persona-chat/reset")
        assert response.status_code == 404


class TestAnalyzeMedicalRecords:
    """测试病历分析 API"""

    def test_analyze_with_text_file(self, test_client, db_session):
        """测试分析文本文件"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="分析医生",
            specialty="内科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建测试文本文件
        content = "患者主诉：头痛三天\n现病史：患者三天前开始出现头痛症状\n诊断：偏头痛\n处方：阿司匹林 100mg 每日一次\n建议：注意休息，避免精神紧张".encode('utf-8')

        files = {"files": ("record.txt", content, "text/plain")}

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == doctor.id
        assert "parsed_files" in data
        assert "features" in data
        assert "generated_prompt" in data
        assert "preview_length" in data

    def test_analyze_with_pdf_file(self, test_client, db_session):
        """测试分析 PDF 文件"""
        from app.models.doctor import Doctor
        from app.models.department import Department
        from PyPDF2 import PdfWriter

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="PDF医生",
            specialty="心内科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建简单 PDF
        pdf_buffer = BytesIO()
        pdf_writer = PdfWriter()
        pdf_writer.add_blank_page(width=200, height=200)
        pdf_writer.write(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        files = {"files": ("record.pdf", pdf_bytes, "application/pdf")}

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == doctor.id

    def test_analyze_multiple_files(self, test_client, db_session):
        """测试分析多个文件"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="多文件医生",
            specialty="综合科",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建多个测试文件
        content1 = "病历1：主诉 头痛".encode('utf-8')
        content2 = "病历2：主诉 发热".encode('utf-8')

        files = [
            ("files", ("record1.txt", content1, "text/plain")),
            ("files", ("record2.txt", content2, "text/plain")),
        ]

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["parsed_files"]) == 2

    def test_analyze_exceeds_file_limit(self, test_client, db_session):
        """测试超过文件数量限制"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="限制医生",
            specialty="测试",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建6个文件（超过限制）
        files = [
            ("files", (f"record{i}.txt", b"content", "text/plain"))
            for i in range(6)
        ]

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 400
        data = response.json()
        assert "5" in data.get("detail", "") or "超过" in data.get("detail", "")

    def test_analyze_single_file_size_exceeds_limit(self, test_client, db_session):
        """测试单文件大小超过限制"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="大小医生",
            specialty="测试",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 创建超过 10MB 的文件
        large_content = b"x" * (10 * 1024 * 1024 + 1)
        files = {"files": ("large.txt", large_content, "text/plain")}

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 400

    def test_analyze_unsupported_format(self, test_client, db_session):
        """测试不支持的文件格式"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="格式医生",
            specialty="测试",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        # 不支持的格式
        content = b"some content"
        files = {"files": ("record.doc", content, "application/msword")}

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/analyze-records",
            files=files
        )

        assert response.status_code == 400

    def test_analyze_nonexistent_doctor(self, test_client):
        """测试分析不存在医生的病历"""
        content = b"test content"
        files = {"files": ("record.txt", content, "text/plain")}

        response = test_client.post(
            "/admin/doctors/99999/analyze-records",
            files=files
        )

        assert response.status_code == 404


class TestSaveAnalysisResult:
    """测试保存病历分析结果"""

    def test_save_analysis_success(self, test_client, db_session):
        """测试成功保存分析结果"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="保存医生",
            specialty="测试",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        prompt = "这是从病历分析生成的 AI 人设提示词"

        response = test_client.post(
            f"/admin/doctors/{doctor.id}/save-analysis",
            data={"ai_persona_prompt": prompt}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "保存" in data["message"]
        assert data["doctor_id"] == doctor.id
        assert data["prompt_length"] == len(prompt)

        # 验证数据库已更新
        db_session.refresh(doctor)
        assert doctor.ai_persona_prompt == prompt

    def test_save_analysis_nonexistent_doctor(self, test_client):
        """测试保存到不存在的医生"""
        response = test_client.post(
            "/admin/doctors/99999/save-analysis",
            data={"ai_persona_prompt": "测试 prompt"}
        )

        assert response.status_code == 404


class TestGetAnalysisStatus:
    """测试获取病历分析状态"""

    def test_get_analysis_status_existing_doctor(self, test_client, db_session):
        """测试获取存在的医生分析状态"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="状态医生",
            specialty="测试",
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.get(f"/admin/doctors/{doctor.id}/analysis-status")

        assert response.status_code == 200
        data = response.json()
        assert data["doctor_id"] == doctor.id
        assert "doctor_name" in data
        assert "records_analyzed" in data
        assert "has_persona_prompt" in data
        assert "prompt_length" in data

    def test_get_analysis_status_with_records_analyzed(self, test_client, db_session):
        """测试已分析病历的医生状态"""
        from app.models.doctor import Doctor
        from app.models.department import Department

        department = Department(name="测试科室", description="测试")
        db_session.add(department)
        db_session.flush()

        doctor = Doctor(
            name="已分析医生",
            specialty="测试",
            ai_persona_prompt="测试提示词",
            records_analyzed=True,
            department_id=department.id
        )
        db_session.add(doctor)
        db_session.commit()

        response = test_client.get(f"/admin/doctors/{doctor.id}/analysis-status")

        assert response.status_code == 200
        data = response.json()
        assert data["records_analyzed"] is True
        assert data["has_persona_prompt"] is True
        assert data["prompt_length"] > 0

    def test_get_analysis_status_nonexistent_doctor(self, test_client):
        """测试获取不存在医生的分析状态"""
        response = test_client.get("/admin/doctors/99999/analysis-status")
        assert response.status_code == 404


class TestRecordAnalysisService:
    """测试病历分析服务（单元测试）"""

    def test_parse_text_file(self):
        """测试解析文本文件"""
        from app.services.record_analysis_service import RecordAnalysisService

        content = "这是测试文本内容\n第二行内容".encode('utf-8')
        result = RecordAnalysisService.parse_file(content, "test.txt")

        assert "测试文本内容" in result
        assert "第二行内容" in result

    def test_parse_pdf_file(self):
        """测试解析 PDF 文件"""
        from app.services.record_analysis_service import RecordAnalysisService
        from PyPDF2 import PdfWriter
        from io import BytesIO

        # 创建包含文字的 PDF
        pdf_buffer = BytesIO()
        pdf_writer = PdfWriter()
        page = pdf_writer.add_blank_page(width=200, height=200)

        # 注意：空白页面没有文字，这里只测试不报错
        pdf_writer.write(pdf_buffer)
        pdf_bytes = pdf_buffer.getvalue()

        result = RecordAnalysisService.parse_file(pdf_bytes, "test.pdf")
        assert isinstance(result, str)

    def test_parse_image_file(self):
        """测试解析图片文件（返回占位符）"""
        from app.services.record_analysis_service import RecordAnalysisService

        content = b"\xff\xd8\xff\xe0"  # JPEG 头部
        result = RecordAnalysisService.parse_file(content, "test.jpg")

        assert "图片" in result or "OCR" in result

    def test_parse_unsupported_file(self):
        """测试解析不支持的文件格式"""
        from app.services.record_analysis_service import RecordAnalysisService

        with pytest.raises(ValueError):
            RecordAnalysisService.parse_file(b"content", "test.doc")

    def test_extract_features_from_text(self):
        """测试从文本提取特征"""
        from app.services.record_analysis_service import RecordAnalysisService

        text = """
        患者主诉：头痛三天
        现病史：患者三天前开始出现头痛，伴有恶心
        诊断：偏头痛
        处方：阿司匹林 100mg 每日一次
        建议：注意休息，规律作息
        复查：一周后复诊
        """

        features = RecordAnalysisService.extract_features(text)

        assert "diagnostic_style" in features
        assert "prescription_habits" in features
        assert "follow_up_pattern" in features
        assert "communication_style" in features
        assert "specialty_focus" in features

    def test_generate_persona_prompt(self):
        """测试生成 AI 人设 Prompt"""
        from app.services.record_analysis_service import RecordAnalysisService

        features = {
            "diagnostic_style": "系统性问诊",
            "prescription_habits": "保守治疗",
            "follow_up_pattern": "定期随访",
            "communication_style": "通俗易懂",
            "specialty_focus": "心血管"
        }

        prompt = RecordAnalysisService.generate_persona_prompt(features, "张医生")

        assert "张医生" in prompt
        assert "系统性问诊" in prompt
        assert "保守治疗" in prompt


class TestPersonaCollectionService:
    """测试对话采集服务（单元测试）"""

    def test_start_collection(self):
        """测试开始采集"""
        from app.services.persona_collection_service import PersonaCollectionService

        import asyncio

        async def run_test():
            greeting = await PersonaCollectionService.start_collection("张医生", "心内科")
            assert "您好" in greeting or "医生分身" in greeting

        asyncio.run(run_test())

    def test_collection_state_serialization(self):
        """测试状态序列化"""
        from app.services.persona_collection_service import CollectionState, CollectionStage

        state = CollectionState()
        state.stage = CollectionStage.SPECIALTY
        state.specialty_focus = "儿科关注点"
        state.communication_style = "温和"

        # 测试 to_dict
        state_dict = state.to_dict()
        assert state_dict["stage"] == "specialty"
        assert state_dict["specialty_focus"] == "儿科关注点"

        # 测试 from_dict
        restored_state = CollectionState.from_dict(state_dict)
        assert restored_state.stage == CollectionStage.SPECIALTY
        assert restored_state.specialty_focus == "儿科关注点"

    def test_process_input_greeting_stage(self):
        """测试处理问候阶段输入"""
        from app.services.persona_collection_service import PersonaCollectionService, CollectionState

        import asyncio

        async def run_test():
            state = CollectionState()
            result = await PersonaCollectionService.process_input(
                "准备好了",
                state,
                "张医生",
                "心内科"
            )

            assert result["stage"] == "specialty"
            assert result["is_complete"] is False

        asyncio.run(run_test())

    def test_generate_summary(self):
        """测试生成总结"""
        from app.services.persona_collection_service import PersonaCollectionService, CollectionState, CollectionStage

        state = CollectionState()
        state.stage = CollectionStage.SUMMARY
        state.specialty_focus = "儿科"
        state.communication_style = "温和"
        state.inquiry_approach = "系统问诊"
        state.prescription_preferences = "保守"
        state.advice_template = "规律作息"

        summary = PersonaCollectionService._generate_summary(state)

        assert "儿科" in summary
        assert "温和" in summary

    def test_generate_persona_prompt(self):
        """测试生成最终的 AI 人设 Prompt"""
        from app.services.persona_collection_service import PersonaCollectionService, CollectionState, CollectionStage

        state = CollectionState()
        state.communication_style = "温和亲切"
        state.inquiry_approach = "先听患者说"
        state.specialty_focus = "儿科疾病"
        state.prescription_preferences = "单一用药"
        state.advice_template = "三分治七分养"

        prompt = PersonaCollectionService._generate_persona_prompt(state, "李医生", "儿科")

        assert "李医生" in prompt
        assert "儿科" in prompt
        assert "温和亲切" in prompt
        assert "先听患者说" in prompt

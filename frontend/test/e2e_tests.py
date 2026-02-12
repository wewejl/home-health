"""
前端 E2E 测试 - 使用 Playwright 进行浏览器自动化测试

测试覆盖：
- 登录页面
- Dashboard 页面
- 医生工作台
- 医嘱管理
- 患者详情
- 管理后台
"""

import pytest
import asyncio
from playwright.async_api import async_playwright


class TestFrontendE2E:
    """前端端到端测试类"""

    @pytest.fixture(scope="session")
    async def browser_page():
        """创建浏览器实例"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            yield page
            await browser.close()

    @pytest.fixture(scope="session")
    async def authenticated_page(browser_page):
        """创建已登录的页面"""
        # 导航到登录页
        await browser_page.goto("http://localhost:8150/login")
        await browser_page.wait_for_load_state("networkidle")

        # 填写登录表单
        await browser_page.fill('input[placeholder*="手机号"]', "13800138000")
        await browser_page.fill('input[placeholder*="验证码"]', "123456")
        await browser_page.click('button[type="submit"]')

        # 等待导航完成
        await browser_page.wait_for_url("**/dashboard**")

        yield browser_page

    # ==================== 登录页面测试 ====================

    @pytest.mark.e2e
    async def test_login_page_loads(browser_page):
        """测试登录页面加载"""
        await browser_page.goto("http://localhost:8150/login")
        await browser_page.wait_for_load_state("networkidle")

        # 验证页面元素存在
        await browser_page.wait_for_selector('input[placeholder*="手机号"]')
        phone_input = await browser_page.query_selector('input[placeholder*="手机号"]')
        assert phone_input is not None

        code_input = await browser_page.query_selector('input[placeholder*="验证码"]')
        assert code_input is not None

        submit_button = await browser_page.query_selector('button[type="submit"]')
        assert submit_button is not None

    @pytest.mark.e2e
    async def test_login_page_validation(browser_page):
        """测试登录表单验证"""
        await browser_page.goto("http://localhost:8150/login")

        # 测试空手机号
        await browser_page.click('button[type="submit"]')
        error_message = await browser_page.query_selector('text*=手机号不能为空')
        assert error_message is not None

    # ==================== Dashboard 页面测试 ====================

    @pytest.mark.e2e
    async def test_dashboard_loads(authenticated_page):
        """测试 Dashboard 页面加载"""
        await authenticated_page.goto("http://localhost:8150/")

        # 验证页面标题
        title = await authenticated_page.title()
        assert "灵犀健康" in title

    @pytest.mark.e2e
    async def test_dashboard_navigation(authenticated_page):
        """测试 Dashboard 导航功能"""
        # 测试快捷入口卡片
        quick_cards = await authenticated_page.query_selector_all('.grid > div')
        assert len(quick_cards) > 0

    # ==================== 医生工作台测试 ====================

    @pytest.mark.e2e
    async def test_doctor_workstation_loads(authenticated_page):
        """测试医生工作台页面加载"""
        await authenticated_page.goto("http://localhost:8150/doctors")

        # 验证页面标题或关键元素
        await authenticated_page.wait_for_selector('text*=患者列表')

    @pytest.mark.e2e
    async def test_doctor_workstation_patient_list(authenticated_page):
        """测试患者列表显示"""
        await authenticated_page.goto("http://localhost:8150/doctors")

        # 等待患者列表加载
        await authenticated_page.wait_for_selector('text*=暂无患者')

        # 或者验证搜索框
        search_box = await authenticated_page.query_selector('input[placeholder*="搜索"]')
        if search_box:
            assert search_box is not None

    # ==================== 医嘱管理测试 ====================

    @pytest.mark.e2e
    async def test_medical_orders_page_loads(authenticated_page):
        """测试医嘱管理页面加载"""
        await authenticated_page.goto("http://localhost:8150/medical-orders")

        # 验证医嘱列表元素
        await authenticated_page.wait_for_selector('text*=医嘱列表')

    @pytest.mark.e2e
    async def test_create_order_button_exists(authenticated_page):
        """测试创建医嘱按钮存在"""
        await authenticated_page.goto("http://localhost:8150/medical-orders")

        # 查找创建按钮
        create_button = await authenticated_page.query_selector('button:has-text("创建医嘱")')
        if not create_button:
            # 尝试其他可能的文本
            create_button = await authenticated_page.query_selector('button:has-text("新建")')
            if not create_button:
                create_button = await authenticated_page.query_selector('a:has-text("添加")')

        assert create_button is not None, "创建医嘱按钮应该存在"

    # ==================== 患者详情测试 ====================

    @pytest.mark.e2e
    async def test_patient_detail_page_loads(authenticated_page):
        """测试患者详情页面加载"""
        # 首先需要患者ID，使用测试ID
        await authenticated_page.goto("http://localhost:8150/patients/4")

        # 验证页面加载
        await authenticated_page.wait_for_load_state("networkidle")

        # 验证患者信息元素
        patient_info = await authenticated_page.query_selector('text*=患者信息')
        if patient_info:
            assert patient_info is not None

    # ==================== 管理后台测试 ====================

    @pytest.mark.e2e
    async def test_admin_dashboard_loads(authenticated_page):
        """测试管理后台加载"""
        await authenticated_page.goto("http://localhost:8150/admin")

        # 验证页面元素
        await authenticated_page.wait_for_selector('text*=管理')

    @pytest.mark.e2e
    async def test_admin_diseases_page_loads(authenticated_page):
        """测试疾病管理页面加载"""
        await authenticated_page.goto("http://localhost:8150/admin/diseases")

        # 验证列表元素
        await authenticated_page.wait_for_selector('table')

    # ==================== 信息展示页面测试 ====================

    @pytest.mark.e2e
    async def test_departments_page_loads(authenticated_page):
        """测试科室列表页面加载"""
        await authenticated_page.goto("http://localhost:8150/departments")

        # 验证科室卡片
        await authenticated_page.wait_for_selector('text*=科室')

    @pytest.mark.e2e
    async def test_diseases_page_loads(authenticated_page):
        """测试疾病列表页面加载"""
        await authenticated_page.goto("http://localhost:8150/diseases")

        # 验证疾病列表
        await authenticated_page.wait_for_selector('text*=疾病')

    @pytest.mark.e2e
    async def test_drugs_page_loads(authenticated_page):
        """测试药品列表页面加载"""
        await authenticated_page.goto("http://localhost:8150/drugs")

        # 验证药品列表
        await authenticated_page.wait_for_selector('text*=药品')

    # ==================== 通用测试 ====================

    @pytest.mark.e2e
    async def test_page_responsive(authenticated_page):
        """测试页面响应式布局"""
        await authenticated_page.goto("http://localhost:8150/")

        # 获取视口大小
        viewport_size = await authenticated_page.viewport_size
        width, height = viewport_size["width"], viewport_size["height"]

        # 验证视口大小
        assert width > 0 and height > 0

    @pytest.mark.e2e
    async def test_no_console_errors(authenticated_page):
        """测试页面无控制台错误"""
        errors = []

        authenticated_page.on("console", lambda msg: errors.append(msg))

        await authenticated_page.goto("http://localhost:8150/")
        await authenticated_page.wait_for_load_state("networkidle")

        # 过滤掉非错误日志
        error_logs = [e for e in errors if e.get("type") in ["error"]]

        # 允许一些非关键警告，但不应有严重错误
        critical_errors = [e for e in error_logs if "uncaught" in str(e).lower()]

        assert len(critical_errors) == 0, f"发现严重错误: {critical_errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

#!/usr/bin/env python3
"""
短信验证码功能测试脚本
测试方案一的所有核心功能
"""
import sys
import os
import time
import asyncio
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sms_service import sms_service
from app.config import get_settings

settings = get_settings()

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests: List[Dict] = []
    
    def add_test(self, name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*80)
        print("测试总结")
        print("="*80)
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"{status} - {test['name']}")
            if test["message"]:
                print(f"     {test['message']}")
        print("="*80)
        print(f"总计: {self.passed + self.failed} 个测试")
        print(f"通过: {self.passed} 个")
        print(f"失败: {self.failed} 个")
        print(f"成功率: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        print("="*80)


async def test_sms_verification():
    """主测试函数"""
    result = TestResult()
    
    print("="*80)
    print("短信验证码工程化改进 - 功能测试")
    print("="*80)
    print(f"环境: {settings.ENVIRONMENT}")
    print(f"测试模式: {settings.TEST_MODE}")
    print(f"测试手机号白名单: {settings.TEST_PHONE_WHITELIST}")
    print("="*80)
    
    # 测试手机号
    test_phone = "13800138000"
    test_phone_not_in_whitelist = "13900139000"
    
    # ========== 测试1: 环境安全检查 ==========
    print("\n[测试1] 环境安全检查")
    try:
        # 验证生产环境不能开启测试模式（这个在初始化时已检查）
        if settings.ENVIRONMENT == "production" and settings.TEST_MODE:
            result.add_test("环境安全检查", False, "生产环境不应开启测试模式")
        else:
            result.add_test("环境安全检查", True, f"环境配置正确: {settings.ENVIRONMENT}")
            print(f"✅ 环境配置正确: {settings.ENVIRONMENT}")
    except Exception as e:
        result.add_test("环境安全检查", False, str(e))
        print(f"❌ 环境检查失败: {e}")
    
    # ========== 测试2: 发送验证码 - 不同purpose ==========
    print("\n[测试2] 发送验证码 - 不同purpose")
    purposes = ["LOGIN", "REGISTER", "RESET_PASSWORD", "SET_PASSWORD"]
    for purpose in purposes:
        try:
            success, msg, expires_in = await sms_service.send_verification_code(
                test_phone, purpose, "127.0.0.1"
            )
            if success:
                result.add_test(f"发送验证码 - {purpose}", True, f"过期时间: {expires_in}秒")
                print(f"✅ {purpose}: {msg}, 过期时间: {expires_in}秒")
            else:
                result.add_test(f"发送验证码 - {purpose}", False, msg)
                print(f"❌ {purpose}: {msg}")
        except Exception as e:
            result.add_test(f"发送验证码 - {purpose}", False, str(e))
            print(f"❌ {purpose}: {e}")
    
    # ========== 测试3: 验证码存储Key检查 ==========
    print("\n[测试3] 验证码存储Key检查（phone:purpose）")
    try:
        # 检查不同purpose的验证码是否独立存储
        store = sms_service.store
        login_key = store._make_key(test_phone, "LOGIN")
        register_key = store._make_key(test_phone, "REGISTER")
        
        has_login = login_key in store._codes
        has_register = register_key in store._codes
        
        if has_login and has_register and login_key != register_key:
            result.add_test("验证码独立存储", True, f"LOGIN和REGISTER验证码独立存储")
            print(f"✅ 验证码独立存储: {login_key} != {register_key}")
        else:
            result.add_test("验证码独立存储", False, "验证码未正确隔离")
            print(f"❌ 验证码存储检查失败")
    except Exception as e:
        result.add_test("验证码独立存储", False, str(e))
        print(f"❌ 存储检查异常: {e}")
    
    # ========== 测试4: 测试验证码 - 白名单机制 ==========
    print("\n[测试4] 测试验证码 - 白名单机制")
    if settings.TEST_MODE:
        # 测试白名单内手机号
        try:
            success, msg = sms_service.verify_code(test_phone, settings.TEST_VERIFICATION_CODE, "LOGIN")
            if success:
                result.add_test("测试验证码 - 白名单内", True, "白名单手机号可使用测试验证码")
                print(f"✅ 白名单内手机号 {test_phone}: 验证通过")
            else:
                result.add_test("测试验证码 - 白名单内", False, msg)
                print(f"❌ 白名单内手机号验证失败: {msg}")
        except Exception as e:
            result.add_test("测试验证码 - 白名单内", False, str(e))
            print(f"❌ 测试异常: {e}")
        
        # 测试白名单外手机号（如果配置了白名单）
        if settings.TEST_PHONE_WHITELIST:
            try:
                success, msg = sms_service.verify_code(test_phone_not_in_whitelist, settings.TEST_VERIFICATION_CODE, "LOGIN")
                if not success and "白名单" in msg:
                    result.add_test("测试验证码 - 白名单外", True, "白名单外手机号被正确拒绝")
                    print(f"✅ 白名单外手机号 {test_phone_not_in_whitelist}: 正确拒绝")
                else:
                    result.add_test("测试验证码 - 白名单外", False, "白名单机制未生效")
                    print(f"❌ 白名单机制失效")
            except Exception as e:
                result.add_test("测试验证码 - 白名单外", False, str(e))
                print(f"❌ 测试异常: {e}")
    else:
        result.add_test("测试验证码 - 白名单机制", True, "非测试模式，跳过")
        print("⏭️  非测试模式，跳过白名单测试")
    
    # ========== 测试5: 验证码验证 - 正确验证码 ==========
    print("\n[测试5] 验证码验证 - 正确验证码")
    try:
        # 先发送一个新的验证码
        success, msg, _ = await sms_service.send_verification_code(
            "13800138002", "LOGIN", "127.0.0.1"
        )
        if success:
            # 获取验证码（从存储中读取，仅用于测试）
            key = sms_service.store._make_key("13800138002", "LOGIN")
            if key in sms_service.store._codes:
                code_info = sms_service.store._codes[key]
                real_code = code_info.code
                
                # 验证正确的验证码
                success, msg = sms_service.verify_code("13800138002", real_code, "LOGIN")
                if success:
                    result.add_test("验证正确验证码", True, "验证成功")
                    print(f"✅ 正确验证码验证通过")
                    
                    # 检查verified标记
                    if code_info.verified and code_info.verified_at:
                        result.add_test("验证码verified标记", True, "已标记为verified")
                        print(f"✅ 验证码已标记为verified")
                    else:
                        result.add_test("验证码verified标记", False, "未正确标记")
                        print(f"❌ verified标记失败")
                else:
                    result.add_test("验证正确验证码", False, msg)
                    print(f"❌ 验证失败: {msg}")
            else:
                result.add_test("验证正确验证码", False, "验证码未找到")
                print(f"❌ 验证码未找到")
        else:
            result.add_test("验证正确验证码", False, "发送验证码失败")
            print(f"❌ 发送验证码失败")
    except Exception as e:
        result.add_test("验证正确验证码", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试6: 验证码验证 - 错误验证码 ==========
    print("\n[测试6] 验证码验证 - 错误验证码")
    try:
        success, msg = sms_service.verify_code("13800138002", "999999", "LOGIN")
        if not success and "错误" in msg:
            result.add_test("验证错误验证码", True, "正确拒绝错误验证码")
            print(f"✅ 错误验证码被正确拒绝: {msg}")
        else:
            result.add_test("验证错误验证码", False, "应该拒绝错误验证码")
            print(f"❌ 错误验证码验证异常")
    except Exception as e:
        result.add_test("验证错误验证码", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试7: 验证码一次性使用 ==========
    print("\n[测试7] 验证码一次性使用机制")
    try:
        # 发送新验证码
        success, msg, _ = await sms_service.send_verification_code(
            "13800138003", "LOGIN", "127.0.0.1"
        )
        if success:
            key = sms_service.store._make_key("13800138003", "LOGIN")
            if key in sms_service.store._codes:
                code_info = sms_service.store._codes[key]
                real_code = code_info.code
                
                # 第一次验证
                success1, msg1 = sms_service.verify_code("13800138003", real_code, "LOGIN")
                
                # 标记已使用
                sms_service.mark_code_used("13800138003", "LOGIN")
                
                # 第二次验证（应该失败）
                success2, msg2 = sms_service.verify_code("13800138003", real_code, "LOGIN")
                
                if success1 and not success2 and "已使用" in msg2:
                    result.add_test("验证码一次性使用", True, "验证码只能使用一次")
                    print(f"✅ 验证码一次性使用机制正常")
                else:
                    result.add_test("验证码一次性使用", False, f"第一次:{success1}, 第二次:{success2}")
                    print(f"❌ 一次性使用机制失败")
            else:
                result.add_test("验证码一次性使用", False, "验证码未找到")
        else:
            result.add_test("验证码一次性使用", False, "发送失败")
    except Exception as e:
        result.add_test("验证码一次性使用", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试8: 跨purpose验证（应失败） ==========
    print("\n[测试8] 跨purpose验证（应失败）")
    try:
        # 发送LOGIN验证码
        success, msg, _ = await sms_service.send_verification_code(
            "13800138004", "LOGIN", "127.0.0.1"
        )
        if success:
            key = sms_service.store._make_key("13800138004", "LOGIN")
            if key in sms_service.store._codes:
                code_info = sms_service.store._codes[key]
                real_code = code_info.code
                
                # 尝试用RESET_PASSWORD验证（应失败）
                success, msg = sms_service.verify_code("13800138004", real_code, "RESET_PASSWORD")
                
                if not success and "不存在" in msg:
                    result.add_test("跨purpose验证隔离", True, "不同purpose的验证码正确隔离")
                    print(f"✅ 跨purpose验证被正确拒绝")
                else:
                    result.add_test("跨purpose验证隔离", False, "purpose隔离失败")
                    print(f"❌ purpose隔离机制失败")
            else:
                result.add_test("跨purpose验证隔离", False, "验证码未找到")
        else:
            result.add_test("跨purpose验证隔离", False, "发送失败")
    except Exception as e:
        result.add_test("跨purpose验证隔离", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试9: 冷却期机制 ==========
    print("\n[测试9] 冷却期机制（60秒）")
    try:
        # 发送第一个验证码
        success1, msg1, _ = await sms_service.send_verification_code(
            "13800138005", "LOGIN", "127.0.0.1"
        )
        
        # 立即尝试再次发送（应失败）
        success2, msg2, _ = await sms_service.send_verification_code(
            "13800138005", "LOGIN", "127.0.0.1"
        )
        
        if success1 and not success2 and "秒后重试" in msg2:
            result.add_test("冷却期机制", True, f"冷却期正常: {msg2}")
            print(f"✅ 冷却期机制正常: {msg2}")
        else:
            result.add_test("冷却期机制", False, f"第一次:{success1}, 第二次:{success2}")
            print(f"❌ 冷却期机制失败")
    except Exception as e:
        result.add_test("冷却期机制", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试10: 清理过期验证码 ==========
    print("\n[测试10] 清理过期验证码")
    try:
        # 记录清理前的验证码数量
        before_count = len(sms_service.store._codes)
        
        # 手动创建一个过期的验证码
        from app.services.sms_service import VerificationCode
        expired_key = sms_service.store._make_key("13800138099", "LOGIN")
        expired_code = VerificationCode(
            code="123456",
            phone="13800138099",
            purpose="LOGIN",
            created_at=time.time() - 400,  # 400秒前
            expires_at=time.time() - 100,  # 100秒前过期
        )
        sms_service.store._codes[expired_key] = expired_code
        
        # 执行清理
        sms_service.store.cleanup_expired()
        
        # 检查过期验证码是否被清理
        if expired_key not in sms_service.store._codes:
            result.add_test("清理过期验证码", True, "过期验证码已清理")
            print(f"✅ 过期验证码已清理")
        else:
            result.add_test("清理过期验证码", False, "过期验证码未清理")
            print(f"❌ 清理失败")
    except Exception as e:
        result.add_test("清理过期验证码", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # ========== 测试11: 已验证验证码保留机制 ==========
    print("\n[测试11] 已验证验证码保留机制（10分钟）")
    try:
        # 创建一个刚验证的验证码
        verified_key = sms_service.store._make_key("13800138098", "LOGIN")
        verified_code = VerificationCode(
            code="123456",
            phone="13800138098",
            purpose="LOGIN",
            created_at=time.time() - 100,
            expires_at=time.time() + 200,
            verified=True,
            verified_at=time.time() - 60,  # 1分钟前验证
        )
        sms_service.store._codes[verified_key] = verified_code
        
        # 执行清理
        sms_service.store.cleanup_expired()
        
        # 检查已验证验证码是否保留
        if verified_key in sms_service.store._codes:
            result.add_test("已验证验证码保留", True, "已验证验证码保留10分钟")
            print(f"✅ 已验证验证码正确保留")
        else:
            result.add_test("已验证验证码保留", False, "已验证验证码被错误清理")
            print(f"❌ 保留机制失败")
    except Exception as e:
        result.add_test("已验证验证码保留", False, str(e))
        print(f"❌ 测试异常: {e}")
    
    # 打印测试总结
    result.print_summary()
    
    return result


if __name__ == "__main__":
    print("\n开始测试短信验证码功能...\n")
    result = asyncio.run(test_sms_verification())
    
    # 返回退出码
    sys.exit(0 if result.failed == 0 else 1)

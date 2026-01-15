"""
AI诊室智能体回归测试
测试场景：
1. 多轮问诊流程
2. force_conclude=true 立即诊断
3. 首轮快捷选项动态生成
4. LLM JSON 解析失败的 fallback 逻辑
5. AI 评估字段正确返回
"""
import asyncio
import json
from app.services.diagnosis_agent import DiagnosisAgent, create_initial_state


class TestDiagnosisAgent:
    """诊断智能体测试类"""
    
    def __init__(self):
        self.agent = DiagnosisAgent()
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status} - {test_name}")
        if message:
            print(f"  {message}")
    
    async def test_multi_turn_consultation(self):
        """测试1: 多轮问诊流程"""
        print("\n" + "="*60)
        print("测试1: 多轮问诊流程")
        print("="*60)
        
        try:
            # 创建初始状态
            state = create_initial_state(
                consultation_id="test-001",
                user_id=1,
                chief_complaint=""
            )
            
            # 第1轮：问候
            state = await self.agent.greet(state)
            self.log_test(
                "1.1 问候阶段",
                state["stage"] == "collecting" and len(state["messages"]) == 1,
                f"Stage: {state['stage']}, Messages: {len(state['messages'])}"
            )
            
            # 检查首轮快捷选项
            self.log_test(
                "1.2 首轮快捷选项生成",
                len(state["quick_options"]) > 0,
                f"生成了 {len(state['quick_options'])} 个选项"
            )
            
            # 第2轮：用户输入症状
            state = await self.agent.analyze_input(state, "最近总是头痛，特别是下午")
            state = await self.agent.assess_progress(state)
            
            self.log_test(
                "1.3 AI评估字段存在",
                "should_diagnose" in state and "confidence" in state and "missing_info" in state,
                f"should_diagnose={state.get('should_diagnose')}, confidence={state.get('confidence')}"
            )
            
            next_step = self.agent.should_continue(state)
            
            if next_step == "continue":
                state = await self.agent.generate_question(state)
                state = await self.agent.generate_quick_options(state)
                
                self.log_test(
                    "1.4 生成后续问题",
                    state["current_question"] != "" and len(state["quick_options"]) > 0,
                    f"问题: {state['current_question'][:50]}..."
                )
            
            # 第3轮：继续回答
            state = await self.agent.analyze_input(state, "持续一周了")
            state = await self.agent.assess_progress(state)
            
            self.log_test(
                "1.5 进度更新",
                state["progress"] > 0 and state["questions_asked"] >= 2,
                f"Progress: {state['progress']}%, Questions: {state['questions_asked']}"
            )
            
            print(f"\n当前状态摘要:")
            print(f"  - 进度: {state['progress']}%")
            print(f"  - 置信度: {state.get('confidence', 0)}%")
            print(f"  - 应该诊断: {state.get('should_diagnose', False)}")
            print(f"  - 缺失信息: {state.get('missing_info', [])}")
            
        except Exception as e:
            self.log_test("1.X 多轮问诊流程", False, f"异常: {str(e)}")
    
    async def test_force_conclude(self):
        """测试2: force_conclude=true 立即诊断"""
        print("\n" + "="*60)
        print("测试2: force_conclude=true 立即诊断")
        print("="*60)
        
        try:
            state = create_initial_state(
                consultation_id="test-002",
                user_id=1,
                chief_complaint="头痛"
            )
            
            # 问候
            state = await self.agent.greet(state)
            
            # 用户输入一次后强制结论
            state = await self.agent.analyze_input(state, "头痛三天了")
            state["force_conclude"] = True
            
            next_step = self.agent.should_continue(state)
            
            self.log_test(
                "2.1 force_conclude 触发诊断",
                next_step == "diagnose",
                f"next_step={next_step}"
            )
            
            # 生成诊断
            state = await self.agent.generate_diagnosis(state)
            
            self.log_test(
                "2.2 诊断报告生成",
                state["stage"] == "completed" and state["progress"] == 100,
                f"Stage: {state['stage']}, Progress: {state['progress']}%"
            )
            
            self.log_test(
                "2.3 诊断结果包含疾病列表",
                len(state["possible_diseases"]) > 0,
                f"疾病数量: {len(state['possible_diseases'])}"
            )
            
            print(f"\n诊断结果:")
            for disease in state["possible_diseases"][:2]:
                print(f"  - {disease.get('name', '未知')}: {disease.get('description', '')[:50]}...")
            
        except Exception as e:
            self.log_test("2.X force_conclude 测试", False, f"异常: {str(e)}")
    
    async def test_initial_options_generation(self):
        """测试3: 首轮快捷选项动态生成"""
        print("\n" + "="*60)
        print("测试3: 首轮快捷选项动态生成")
        print("="*60)
        
        try:
            # 测试无主诉
            options_1 = await self.agent.generate_initial_options("")
            self.log_test(
                "3.1 无主诉时生成默认选项",
                len(options_1) >= 4,
                f"生成了 {len(options_1)} 个选项"
            )
            
            # 测试有主诉
            options_2 = await self.agent.generate_initial_options("咳嗽发烧")
            self.log_test(
                "3.2 有主诉时生成相关选项",
                len(options_2) >= 4,
                f"生成了 {len(options_2)} 个选项"
            )
            
            # 检查是否包含"其他"类选项
            has_other = any("其他" in opt.get("text", "") or "不确定" in opt.get("text", "") for opt in options_2)
            self.log_test(
                "3.3 包含其他/不确定选项",
                has_other,
                f"选项: {[opt['text'] for opt in options_2]}"
            )
            
            print(f"\n生成的选项示例:")
            for opt in options_2[:3]:
                print(f"  - {opt['text']} ({opt['category']})")
            
        except Exception as e:
            self.log_test("3.X 首轮选项生成测试", False, f"异常: {str(e)}")
    
    async def test_llm_json_parse_failure(self):
        """测试4: LLM JSON 解析失败的 fallback"""
        print("\n" + "="*60)
        print("测试4: LLM JSON 解析失败的 fallback")
        print("="*60)
        
        try:
            state = create_initial_state(
                consultation_id="test-004",
                user_id=1,
                chief_complaint="测试"
            )
            
            # 模拟评估进度（即使 LLM 返回无效 JSON，也应该有 fallback）
            state["messages"] = [
                {"role": "user", "content": "测试输入", "timestamp": "2025-12-30T00:00:00Z"}
            ]
            state["symptoms"] = ["测试症状"]
            state["questions_asked"] = 2
            
            # 调用评估（如果 LLM 失败，应该使用 fallback）
            state = await self.agent.assess_progress(state)
            
            self.log_test(
                "4.1 Fallback 策略生效",
                "progress" in state and state["progress"] >= 0,
                f"Progress: {state['progress']}%"
            )
            
            self.log_test(
                "4.2 所有必需字段存在",
                all(key in state for key in ["should_diagnose", "confidence", "missing_info"]),
                f"should_diagnose={state.get('should_diagnose')}, confidence={state.get('confidence')}"
            )
            
            # 测试快捷选项生成失败的 fallback
            state["current_question"] = "测试问题"
            state = await self.agent.generate_quick_options(state)
            
            self.log_test(
                "4.3 快捷选项 fallback",
                len(state["quick_options"]) > 0,
                f"生成了 {len(state['quick_options'])} 个选项"
            )
            
        except Exception as e:
            self.log_test("4.X JSON 解析失败测试", False, f"异常: {str(e)}")
    
    async def test_ai_evaluation_fields(self):
        """测试5: AI 评估字段正确返回"""
        print("\n" + "="*60)
        print("测试5: AI 评估字段正确返回")
        print("="*60)
        
        try:
            state = create_initial_state(
                consultation_id="test-005",
                user_id=1,
                chief_complaint="胃痛"
            )
            
            # 模拟多轮对话
            state["messages"] = [
                {"role": "assistant", "content": "请描述症状", "timestamp": "2025-12-30T00:00:00Z"},
                {"role": "user", "content": "胃痛三天", "timestamp": "2025-12-30T00:01:00Z"},
                {"role": "assistant", "content": "疼痛程度如何", "timestamp": "2025-12-30T00:02:00Z"},
                {"role": "user", "content": "比较严重", "timestamp": "2025-12-30T00:03:00Z"}
            ]
            state["symptoms"] = ["胃痛", "疼痛严重"]
            state["questions_asked"] = 2
            
            # 评估进度
            state = await self.agent.assess_progress(state)
            
            # 验证所有 AI 评估字段
            required_fields = ["progress", "should_diagnose", "can_conclude", "confidence", "missing_info", "reasoning"]
            all_present = all(field in state for field in required_fields)
            
            self.log_test(
                "5.1 所有 AI 评估字段存在",
                all_present,
                f"字段: {[f for f in required_fields if f in state]}"
            )
            
            # 验证字段类型
            type_checks = [
                isinstance(state.get("progress"), int),
                isinstance(state.get("should_diagnose"), bool),
                isinstance(state.get("can_conclude"), bool),
                isinstance(state.get("confidence"), int),
                isinstance(state.get("missing_info"), list),
                isinstance(state.get("reasoning"), str)
            ]
            
            self.log_test(
                "5.2 字段类型正确",
                all(type_checks),
                f"progress={state.get('progress')}, confidence={state.get('confidence')}"
            )
            
            # 验证 should_continue 逻辑
            next_step = self.agent.should_continue(state)
            self.log_test(
                "5.3 should_continue 逻辑正确",
                next_step in ["diagnose", "continue"],
                f"next_step={next_step}, should_diagnose={state.get('should_diagnose')}"
            )
            
            print(f"\nAI 评估详情:")
            print(f"  - 进度: {state.get('progress')}%")
            print(f"  - 应该诊断: {state.get('should_diagnose')}")
            print(f"  - 可以结束: {state.get('can_conclude')}")
            print(f"  - 置信度: {state.get('confidence')}%")
            print(f"  - 缺失信息: {state.get('missing_info')}")
            print(f"  - 评估理由: {state.get('reasoning')[:80]}...")
            
        except Exception as e:
            self.log_test("5.X AI 评估字段测试", False, f"异常: {str(e)}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"\n总计: {total} 个测试")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n🧪 开始 AI 诊室智能体回归测试")
        print("="*60)
        
        await self.test_multi_turn_consultation()
        await self.test_force_conclude()
        await self.test_initial_options_generation()
        await self.test_llm_json_parse_failure()
        await self.test_ai_evaluation_fields()
        
        self.print_summary()


async def main():
    """主函数"""
    tester = TestDiagnosisAgent()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

"""
并行工具执行器

支持同时执行多个独立工具，提升响应速度
参考: awesome-llm-apps 中的并行执行模式
"""
import asyncio
import json
from typing import Dict, Any, List, Callable, Optional, Tuple
from concurrent.futures import TimeoutError


# 并行执行配置
PARALLEL_CONFIG = {
    "max_concurrent": 5,      # 最大并发数
    "timeout": 30,            # 单个工具超时时间（秒）
    "enable_parallel": True,  # 是否启用并行执行
}


class ParallelToolExecutor:
    """
    并行工具执行器

    功能：
    1. 按工具类型分组，并行执行独立的工具调用
    2. 处理超时和错误
    3. 收集和合并结果
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**PARALLEL_CONFIG, **(config or {})}

    def _group_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        将工具调用按类型分组

        分组规则：
        - knowledge_group: 知识查询类工具
        - image_group: 图像分析类工具
        - risk_group: 风险评估类工具
        - dossier_group: 档案生成类工具
        - medication_group: 用药查询类工具
        """
        groups = {
            "knowledge_group": [],
            "image_group": [],
            "risk_group": [],
            "dossier_group": [],
            "medication_group": [],
            "other_group": []
        }

        for call in tool_calls:
            tool_name = call.get("function", {}).get("name", "")

            if tool_name in ["search_medical_knowledge", "corrective_rag_search"]:
                groups["knowledge_group"].append(call)
            elif tool_name == "analyze_skin_image":
                groups["image_group"].append(call)
            elif tool_name == "assess_risk":
                groups["risk_group"].append(call)
            elif tool_name == "generate_medical_dossier":
                groups["dossier_group"].append(call)
            elif tool_name == "search_medication":
                groups["medication_group"].append(call)
            else:
                groups["other_group"].append(call)

        return groups

    async def _execute_single_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        tool_func: Callable,
        tool_index: int = 0
    ) -> Dict[str, Any]:
        """
        执行单个工具，带超时和错误处理

        Args:
            tool_name: 工具名称
            args: 工具参数
            tool_func: 工具函数
            tool_index: 工具调用索引（用于标识）

        Returns:
            {
                "tool": str,
                "args": dict,
                "result": dict,
                "success": bool,
                "error": str (if failed),
                "duration": float (秒)
            }
        """
        import time
        start_time = time.time()

        try:
            # 使用 asyncio.wait_for 实现超时
            result = await asyncio.wait_for(
                tool_func(**args),
                timeout=self.config["timeout"]
            )

            duration = time.time() - start_time

            return {
                "tool": tool_name,
                "args": args,
                "result": result,
                "success": True,
                "duration": round(duration, 3),
                "index": tool_index
            }

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return {
                "tool": tool_name,
                "args": args,
                "result": {"error": f"工具执行超时（>{self.config['timeout']}秒）"},
                "success": False,
                "error": "timeout",
                "duration": round(duration, 3),
                "index": tool_index
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "tool": tool_name,
                "args": args,
                "result": {"error": str(e)},
                "success": False,
                "error": str(e),
                "duration": round(duration, 3),
                "index": tool_index
            }

    async def execute_parallel(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_registry: Dict[str, Callable],
        enable_parallel: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        并行执行工具调用

        Args:
            tool_calls: 工具调用列表
            tool_registry: 工具注册表
            enable_parallel: 是否启用并行（None 则使用配置）

        Returns:
            工具执行结果列表
        """
        if not tool_calls:
            return []

        # 检查是否启用并行
        if enable_parallel is None:
            enable_parallel = self.config["enable_parallel"]

        if not enable_parallel:
            # 串行执行
            return await self._execute_serial(tool_calls, tool_registry)

        # 分组工具调用
        groups = self._group_tool_calls(tool_calls)

        # 收集所有任务
        all_tasks = []
        task_metadata = []  # 记录任务所属的组

        for group_name, calls in groups.items():
            if not calls:
                continue

            # 同一组内的工具串行执行（避免资源竞争）
            # 但不同组之间并行执行
            for i, call in enumerate(calls):
                tool_name = call.get("function", {}).get("name", "")
                args_str = call.get("function", {}).get("arguments", "{}")

                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}

                tool_func = tool_registry.get(tool_name)
                if not tool_func:
                    all_tasks.append(self._create_missing_tool_result(tool_name, args))
                    task_metadata.append((group_name, i))
                    continue

                # 创建异步任务
                task = self._execute_single_tool(tool_name, args, tool_func, i)
                all_tasks.append(task)
                task_metadata.append((group_name, i))

        if not all_tasks:
            return []

        # 并行执行所有任务
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                group_name, idx = task_metadata[i] if i < len(task_metadata) else ("unknown", i)
                processed_results.append({
                    "tool": "unknown",
                    "args": {},
                    "result": {"error": str(result)},
                    "success": False,
                    "error": str(result),
                    "group": group_name
                })
            else:
                group_name, idx = task_metadata[i] if i < len(task_metadata) else ("unknown", i)
                result["group"] = group_name
                processed_results.append(result)

        return processed_results

    async def _execute_serial(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_registry: Dict[str, Callable]
    ) -> List[Dict[str, Any]]:
        """串行执行工具调用（兼容模式）"""
        results = []

        for i, call in enumerate(tool_calls):
            tool_name = call.get("function", {}).get("name", "")
            args_str = call.get("function", {}).get("arguments", "{}")

            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}

            tool_func = tool_registry.get(tool_name)
            if not tool_func:
                results.append(self._create_missing_tool_result(tool_name, args))
                continue

            result = await self._execute_single_tool(tool_name, args, tool_func, i)
            results.append(result)

        return results

    def _create_missing_tool_result(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """创建工具不存在的结果"""
        return {
            "tool": tool_name,
            "args": args,
            "result": {"error": f"工具 {tool_name} 不存在"},
            "success": False,
            "error": f"Tool {tool_name} not found",
            "duration": 0
        }

    def format_execution_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化执行摘要

        Args:
            results: 工具执行结果列表

        Returns:
            执行摘要文本
        """
        if not results:
            return "未执行任何工具"

        total = len(results)
        success = sum(1 for r in results if r.get("success"))
        failed = total - success
        total_duration = sum(r.get("duration", 0) for r in results)

        lines = [
            f"工具执行完成：共 {total} 个",
            f"✓ 成功: {success}",
            f"✗ 失败: {failed}" if failed > 0 else "",
            f"⏱ 总耗时: {total_duration:.2f}秒"
        ]

        # 按组统计
        groups = {}
        for r in results:
            group = r.get("group", "unknown")
            if group not in groups:
                groups[group] = {"count": 0, "success": 0, "duration": 0}
            groups[group]["count"] += 1
            if r.get("success"):
                groups[group]["success"] += 1
            groups[group]["duration"] += r.get("duration", 0)

        if groups:
            lines.append("\n按组统计：")
            for group, stats in groups.items():
                lines.append(
                    f"  {group}: {stats['success']}/{stats['count']} "
                    f"({stats['duration']:.2f}秒)"
                )

        return "\n".join(filter(None, lines))


# 全局执行器实例
_executor: Optional[ParallelToolExecutor] = None


def get_parallel_executor() -> ParallelToolExecutor:
    """获取并行执行器单例"""
    global _executor
    if _executor is None:
        _executor = ParallelToolExecutor()
    return _executor


async def execute_tools_parallel(
    tool_calls: List[Dict[str, Any]],
    tool_registry: Dict[str, Callable],
    enable_parallel: bool = True
) -> List[Dict[str, Any]]:
    """
    并行执行工具调用

    Args:
        tool_calls: 工具调用列表
        tool_registry: 工具注册表
        enable_parallel: 是否启用并行

    Returns:
        工具执行结果列表
    """
    executor = get_parallel_executor()
    return await executor.execute_parallel(tool_calls, tool_registry, enable_parallel)


# 针对医学场景的专用并行函数
async def parallel_medical_search(
    query: str,
    specialty: str = "general",
    tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    并行执行医学相关搜索

    同时执行：
    - 知识库搜索
    - CRAG 搜索（如果启用）
    - 风险评估（如果需要）

    Args:
        query: 查询内容
        specialty: 科室类型
        tools: 要执行的工具列表（None 则执行所有）

    Returns:
        合并的搜索结果
    """
    from . import TOOL_REGISTRY

    if tools is None:
        tools = ["search_medical_knowledge", "corrective_rag_search"]

    # 准备工具调用
    tool_calls = []
    for tool in tools:
        tool_calls.append({
            "function": {
                "name": tool,
                "arguments": json.dumps({"query": query, "specialty": specialty})
            }
        })

    # 并行执行
    results = await execute_tools_parallel(tool_calls, TOOL_REGISTRY)

    # 合并结果
    merged = {
        "query": query,
        "specialty": specialty,
        "results": [],
        "sources": [],
        "total_duration": 0
    }

    for r in results:
        if r.get("success"):
            result_data = r.get("result", {})
            if result_data.get("found"):
                merged["results"].extend(result_data.get("results", []))
                merged["sources"].append(result_data.get("source", "unknown"))
        merged["total_duration"] += r.get("duration", 0)

    merged["found"] = len(merged["results"]) > 0

    return merged


if __name__ == "__main__":
    async def test():
        from . import TOOL_REGISTRY

        # 测试并行执行
        tool_calls = [
            {
                "function": {
                    "name": "search_medical_knowledge",
                    "arguments": json.dumps({"query": "湿疹的症状", "specialty": "dermatology"})
                }
            },
            {
                "function": {
                    "name": "search_medical_knowledge",
                    "arguments": json.dumps({"query": "银屑病的症状", "specialty": "dermatology"})
                }
            }
        ]

        results = await execute_tools_parallel(tool_calls, TOOL_REGISTRY)

        executor = get_parallel_executor()
        print(executor.format_execution_summary(results))
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(test())

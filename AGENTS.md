# 员工执行法则 (The Laws of Physics)
本法则是整个岁月梦工厂的底层物理规律。所有文档输出默认使用中文。

---

## 角色判断（硬规则）
- `sessions_spawn` 唤起 + task含 `[ROLE:EXECUTOR]` → **执行节点模式** → `read data/EXECUTOR-RULES.md`
- 否则 → **CEO模式**，遵循 `SOUL.md`（复杂任务 → `read data/CEO-STATE-MACHINE.md`）

## CEO模式要点
* 遵循 `SOUL.md` 核心人设与状态机
* 派发协议：`runtime: "subagent", mode: "run"`，task以 `[ROLE:EXECUTOR]` 开头
* 严禁让子智能体继承主对话历史；平台报错 → 降级 `exec`

## 全员通用协议
1. **记忆协议**：高价值信息 → `memory_store`；上下文无答案 → `memory_recall`
2. **重启遗书**：重启网关前写 `BOOT.md`，note参数包含恢复指令
3. **持久化**：Context=RAM(易失)，Filesystem=Disk(持久)。每2次重要操作写入文件
4. **输出格式**：Discord用Markdown+Emoji；网页抓取失败 → browser截图

> 收到开发需求时，先 `read DEV-SOP.md` 查阅完整开发闭环协议。

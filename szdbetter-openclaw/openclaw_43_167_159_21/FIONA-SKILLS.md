# Fiona 物理节点与跨界技能

## Fiona 物理节点 (The Physical Mechanical Arm)
**Fiona 是一台没有独立思考能力的物理执行服务器（Node）。** 任何模型需要与真实世界交互时，必须遥控 Fiona：
* **定位**：Fiona 只负责执行脚本和挂载高频爬虫、监控任务。
* **调用指令**：所有涉及到需要在本地机器上运行代码、启动持续监控脚本的任务，必须使用 `exec` 工具，并强制附加参数：`host="node", node="fiona"`。
* **标准工作流**：先写好高可用脚本 -> 审查无误 -> 调用 `exec host=node node=fiona` 下发运行 -> 长驻任务设置 `background: true`。

## 跨界特种能力 (Skills / Tools)
纯文本模型没有嘴巴和眼睛，遇到以下需求，必须精准调用外部技能：
* **生成语音**：使用 `tts` 工具或 `sag` 技能（ElevenLabs）。
* **画图制表**：使用 `nano-banana-pro` 技能（Imagen 4）。
* **日程邮件**：使用 `gog` 技能 (Google Suite)。
* **推特搜索**：使用 `bird` 技能或 Jina Reader 爬取。

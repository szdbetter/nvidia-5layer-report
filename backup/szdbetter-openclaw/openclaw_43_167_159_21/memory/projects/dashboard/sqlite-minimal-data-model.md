# SQLite 最小数据模型

## 1. missions
- id TEXT PRIMARY KEY
- name TEXT NOT NULL
- owner TEXT
- sponsor TEXT
- priority TEXT
- status TEXT
- roi_hypothesis TEXT
- mission_text TEXT
- deliverables TEXT
- non_goals TEXT
- deadline TEXT
- acceptance_criteria TEXT
- evidence_requirements TEXT
- failure_conditions TEXT
- risk_level TEXT
- current_phase TEXT
- next_action TEXT
- created_at TEXT
- updated_at TEXT

## 2. mission_resources
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- resource_type TEXT   -- node/model/tool/api/permission/budget
- resource_name TEXT
- details TEXT

## 3. mission_assignments
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- actor_type TEXT      -- reese/fiona/acp/subagent/human
- actor_name TEXT
- responsibility TEXT
- status TEXT

## 4. mission_events
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- event_type TEXT      -- created/updated/blocked/review/done/alert/memory_write
- event_text TEXT
- source TEXT
- created_at TEXT

## 5. artifacts
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- artifact_type TEXT   -- file/log/screenshot/report/data/pr/issue/run
- title TEXT
- path_or_ref TEXT
- summary TEXT
- created_at TEXT

## 6. runtime_entities
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- entity_type TEXT     -- session/subagent/process/cron/node
- entity_key TEXT
- label TEXT
- status TEXT
- last_seen_at TEXT
- last_summary TEXT

## 7. risks
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- risk_type TEXT
- severity TEXT
- description TEXT
- mitigation TEXT
- escalated INTEGER
- updated_at TEXT

## 8. memories
- id INTEGER PRIMARY KEY AUTOINCREMENT
- mission_id TEXT
- memory_query TEXT
- memory_summary TEXT
- recall_score REAL
- recall_status TEXT
- stored_at TEXT

## 9. audit_logs
- id INTEGER PRIMARY KEY AUTOINCREMENT
- action TEXT
- target_type TEXT
- target_id TEXT
- actor TEXT
- details TEXT
- created_at TEXT

## 设计原则
- 先能审计，再谈自动化
- 先支持任务与证据闭环，再扩展复杂控制能力
- mission_id 为全局主键，贯穿文档、状态、证据、记忆、运行实体

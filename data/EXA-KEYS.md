# EXA API Keys（自动轮换）

共 6 个 key，存于 `/root/.openclaw/.env`，按序轮换，用完切下一个，全部耗尽时提醒用户：

- `EXA_API_KEY1` = 49cd5c33-...（末尾 22ce）
- `EXA_API_KEY2` = 6d401104-...（末尾 44d3）
- `EXA_API_KEY3` = e49c28c9-...（末尾 22ce）
- `EXA_API_KEY4` = 6dc9bd44-...（末尾 9bdf）
- `EXA_API_KEY5` = 06cc66ff-...（末尾 9339）
- `EXA_API_KEY6` = 936614d2-...（末尾 8109）

**轮换策略：** 依次尝试 KEY1→KEY6；收到 429 / quota exceeded 错误时切换下一个；全部失败时发 Discord 提醒。

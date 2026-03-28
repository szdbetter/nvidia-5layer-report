import os
# 调用系统工具发送测试消息
os.system('openclaw message send --channel discord --target 1472858439591002211 --message "✅ [System Test] 守护进程通信链路测试：成功。"')
print("Test command sent.")

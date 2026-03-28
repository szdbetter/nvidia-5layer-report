#!/usr/bin/env python3
"""
claude_stream_discord.py - PTY方式启动claude，逐行流式输出到文件+终端
用法: python3 claude_stream_discord.py "<prompt>" [output_file]
输出文件由外部（openclaw agent）轮询读取并转发到Discord
"""
import sys, os, pty, select, time, subprocess

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "你好"
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/claude_stream.log"
MARKER = "/tmp/claude_stream.done"

def main():
    cmd = ["claude", "--print", "--max-turns", "5", PROMPT]
    
    # 清理旧文件
    for f in [OUTFILE, MARKER]:
        if os.path.exists(f):
            os.remove(f)
    
    # 写入启动标记
    with open(OUTFILE, "w") as f:
        f.write(f"🚀 Claude Code 开始执行\n$ {' '.join(cmd)}\n---\n")
        f.flush()
    
    # 用PTY启动claude
    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(cmd, stdout=slave_fd, stderr=slave_fd,
                            stdin=subprocess.DEVNULL, close_fds=True)
    os.close(slave_fd)
    
    print(f"[stream] PID={proc.pid}", flush=True)
    
    with open(OUTFILE, "a") as outf:
        try:
            while True:
                ready, _, _ = select.select([master_fd], [], [], 0.5)
                if ready:
                    try:
                        data = os.read(master_fd, 4096).decode("utf-8", errors="replace")
                    except OSError:
                        break
                    if not data:
                        break
                    # 过滤ANSI控制码
                    import re
                    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b\[\?[0-9;]*[a-zA-Z]', '', data)
                    print(clean, end="", flush=True)
                    outf.write(clean)
                    outf.flush()
                
                if proc.poll() is not None:
                    try:
                        while True:
                            ready, _, _ = select.select([master_fd], [], [], 0.1)
                            if not ready:
                                break
                            data = os.read(master_fd, 4096).decode("utf-8", errors="replace")
                            if not data:
                                break
                            import re
                            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b\[\?[0-9;]*[a-zA-Z]', '', data)
                            print(clean, end="", flush=True)
                            outf.write(clean)
                            outf.flush()
                    except OSError:
                        pass
                    break
        finally:
            os.close(master_fd)
    
    exit_code = proc.wait()
    # 写完成标记
    with open(MARKER, "w") as f:
        f.write(f"exit={exit_code}\n")
    
    print(f"\n[stream] exit={exit_code}", flush=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bot monitor: tail openclaw logs, detect errors, write status JSON, alert Discord."""

import json
import os
import re
import time
import subprocess
from datetime import datetime, timezone

STATUS_FILE = '/tmp/bot_monitor_status.json'
ENV_FILE = '/root/.openclaw/.env'
NOTIFY_USER_ID = '825020287162122302'
COOLDOWN_SECS = 600  # 10 min between alerts per channel
SCAN_LINES = 500
INTERVAL = 30

RE_FAILOVER = re.compile(r'FailoverError')
RE_LANE_ERROR = re.compile(r'lane task error:.*?lane=session:agent:primary:discord:channel:(\d+)')
RE_LANE_TIMEOUT = re.compile(r'lane wait exceeded.*?lane=session:agent:primary:discord:channel:(\d+)')
RE_WORKER_TIMEOUT = re.compile(r'discord inbound worker timed out')

last_alert_ts = {}
notify_disabled = set()  # channels that returned 403, skip permanently


def load_env():
    env = {}
    try:
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


def get_log_path():
    today = datetime.now().strftime('%Y-%m-%d')
    return f'/tmp/openclaw/openclaw-{today}.log'


def get_recent_lines(path, n):
    try:
        result = subprocess.run(['tail', '-n', str(n), path], capture_output=True, text=True, timeout=5)
        return result.stdout.splitlines()
    except Exception:
        return []


def send_discord_notify(token, channel_id, message):
    """Send notification message to a specific Discord channel. Returns 'ok', 'forbidden', or 'error'."""
    try:
        import urllib.request
        req = urllib.request.Request(
            f'https://discord.com/api/v10/channels/{channel_id}/messages',
            data=json.dumps({'content': message}).encode(),
            headers={'Authorization': f'Bot {token}', 'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        return 'ok'
    except Exception as e:
        msg = str(e)
        if '403' in msg:
            return 'forbidden'
        print(f'[bot-monitor] Discord notify failed for channel {channel_id}: {e}')
        return 'error'


def analyze(lines):
    channel_errors = {}  # channel_id -> {'count': int, 'type': str}
    failover_count = 0
    worker_timeouts = 0

    for line in lines:
        if RE_FAILOVER.search(line):
            failover_count += 1

        m = RE_LANE_ERROR.search(line)
        if m:
            ch = m.group(1)
            entry = channel_errors.setdefault(ch, {'count': 0, 'type': 'lane_error'})
            entry['count'] += 1

        m = RE_LANE_TIMEOUT.search(line)
        if m:
            ch = m.group(1)
            entry = channel_errors.setdefault(ch, {'count': 0, 'type': 'timeout'})
            entry['count'] += 1
            entry['type'] = 'timeout'

        if RE_WORKER_TIMEOUT.search(line):
            worker_timeouts += 1

    return failover_count, worker_timeouts, channel_errors


def main():
    print('[bot-monitor] Starting...')
    env = load_env()
    discord_token = env.get('DISCORD_TOKEN', '')

    while True:
        try:
            log_path = get_log_path()
            lines = get_recent_lines(log_path, SCAN_LINES)
            failover_count, worker_timeouts, channel_errors = analyze(lines)
            now_iso = datetime.now(timezone.utc).isoformat()

            total_errors = sum(v['count'] for v in channel_errors.values())
            if failover_count > 100 or worker_timeouts > 0:
                health = 'degraded'
            elif total_errors > 0:
                health = 'warning'
            else:
                health = 'ok'

            status = {
                'ok': health == 'ok',
                'health': health,
                'failover_count': failover_count,
                'worker_timeouts': worker_timeouts,
                'channel_errors': channel_errors,
                'lines_scanned': len(lines),
                'checked_at': now_iso,
            }

            with open(STATUS_FILE, 'w') as f:
                json.dump(status, f)

            # Send Discord alerts with cooldown — send to the affected channel itself
            if discord_token:
                for ch_id, err in channel_errors.items():
                    if err['count'] >= 5 and ch_id not in notify_disabled:
                        last = last_alert_ts.get(ch_id, 0)
                        if time.time() - last > COOLDOWN_SECS:
                            msg = (
                                f'📡 **[Bot监控]** 频道最近 {SCAN_LINES} 行日志检测到 {err["count"]} 次 API 错误（{err["type"]}）\n'
                                f'Failover总计: {failover_count} | 如持续请等待或重置会话'
                            )
                            result = send_discord_notify(discord_token, ch_id, msg)
                            if result == 'ok':
                                last_alert_ts[ch_id] = time.time()
                                print(f'[bot-monitor] Alerted channel {ch_id}')
                            elif result == 'forbidden':
                                print(f'[bot-monitor] Channel {ch_id} not writable (403), disabling notifications')
                                notify_disabled.add(ch_id)

        except Exception as e:
            print(f'[bot-monitor] Error: {e}')

        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()

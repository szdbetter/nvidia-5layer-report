#!/bin/bash
# 自动检查 Bounty 支付状态并发送邮件提醒
source "/root/.openclaw/workspace/config/.secrets"

CHECK_URL="https://api.agentcoin.site/v1/payouts/$RTC_WALLET_ADDRESS"
LOG_FILE="logs/bounty_payout.log"

response=$(curl -s $CHECK_URL)
status=$(echo $response | jq -r '.status')

if [ "$status" == "paid" ]; then
    amount=$(echo $response | jq -r '.amount')
    tx_hash=$(echo $response | jq -r '.tx_hash')
    
    # 发送邮件提醒
    message="岁月老板，Bounty 赏金已到账！金额: $amount RTC, 交易哈希: $tx_hash"
    
    # 尝试使用第一个 Resend Key
    curl -X POST https://api.resend.com/emails       -H "Authorization: Bearer $RESEND_API_KEY_1"       -H "Content-Type: application/json"       -d '{
        "from": "Reese <onboarding@resend.dev>",
        "to": "8044372@gmail.com",
        "subject": "💰 Bounty 赏金到账提醒",
        "html": "'"$message"'"
      }'
      
    echo "$(date): Paid $amount RTC" >> $LOG_FILE
fi

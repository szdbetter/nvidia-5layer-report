const WebSocket = require('ws');

// 替换为你最核心的 3 个聪明钱地址（测试用）
const SMART_MONEY_ADDRESSES = [
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pT8hq", // 示例地址1
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  // 示例地址2
];

// 生产环境必须使用 Helius 或 QuickNode 的 WSS 专属节点，公开节点会限流
const SOLANA_WSS_URL = 'wss://api.mainnet-beta.solana.com/'; 

const ws = new WebSocket(SOLANA_WSS_URL);

ws.on('open', function open() {
    console.log('🟢 [Reese 监控系统] 已连接至 Solana WSS 节点');
    
    // 遍历聪明钱地址，建立监听订阅
    SMART_MONEY_ADDRESSES.forEach(address => {
        const subscribeMessage = JSON.stringify({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                { "mentions": [address] },
                { "commitment": "processed" } // 使用 processed 级别，获取最快（毫秒级）的未确认交易
            ]
        });
        ws.send(subscribeMessage);
        console.log(`📡 [监听启动] 锁定聪明钱地址: ${address}`);
    });
});

ws.on('message', function incoming(data) {
    const response = JSON.parse(data);
    if (response.method === 'logsNotification') {
        const log = response.params.result;
        console.log('\n🚨 [异动警报] 聪明钱发起交易!');
        console.log(`签名 (TxHash): https://solscan.io/tx/${log.value.signature}`);
        
        // 解析日志寻找 Swap 特征词
        const isSwap = log.value.logs.some(l => l.includes('Swap') || l.includes('Raydium') || l.includes('Pump'));
        if (isSwap) {
            console.log('🔥 判定为【买入/卖出 Swap 操作】！立即启动跟随逻辑...');
            // TODO: 这里接入后续的自动买入合约逻辑
        }
    }
});

ws.on('close', function close() {
    console.log('🔴 [系统] WSS 连接断开，尝试重连...');
});

// 运行方式: node smart_money_monitor.js

const { TelegramClient } = require("telegram");
const { StringSession } = require("telegram/sessions");
const fs = require('fs');

const apiId = 6;
const apiHash = "eb06d4abfb49dc3eeb1aeb98ae0f581e";
const path = require('path');
const sessionPath = path.join(__dirname, 'session.txt');
const sessionString = fs.readFileSync(sessionPath, 'utf8').trim();
const stringSession = new StringSession(sessionString);

// 目标频道列表
const CHANNELS = [
  '-1003434262323', // Crypto Market Aggregator
  '-1002364176580', // 方程式财经
  '-1001602580600', // Sea 哥币圈日志
  '-1001198046393', // Pow's Gem Calls
  '-1001973272550', // Pendle 中文
  '-1002628325682', // Wendy‘s Alpha
  '-1002955560057', // AU Trading Journal
  '-1002205515142', // Alex 投资备忘
  '-1002631914757', // 投机之路
  '-1001875205924'  // 链上星光
];

(async () => {
  const client = new TelegramClient(stringSession, apiId, apiHash, {
    connectionRetries: 5,
  });

  await client.connect();

  // 获取时间限制（默认过去 24 小时，如果是 cron 调用可以通过参数控制）
  const hours = process.argv[2] ? parseInt(process.argv[2]) : 24;
  const cutoff = Date.now() / 1000 - (hours * 3600);

  const results = {};

  for (const chatId of CHANNELS) {
      try {
          const entity = await client.getEntity(chatId);
          const name = entity.title || entity.username || chatId;
          
          const messages = await client.getMessages(entity, { limit: 20 });
          const recentMsgs = [];

          for (const msg of messages) {
              if (msg.date > cutoff && msg.message) {
                  recentMsgs.push({
                      date: new Date(msg.date * 1000).toLocaleString(),
                      text: msg.message
                  });
              }
          }

          if (recentMsgs.length > 0) {
              results[name] = recentMsgs;
          }
      } catch (e) {
          console.error(`Error fetching ${chatId}: ${e.message}`);
      }
  }

  // 输出 JSON 供 Agent 处理
  console.log(JSON.stringify(results, null, 2));
  process.exit(0);
})();

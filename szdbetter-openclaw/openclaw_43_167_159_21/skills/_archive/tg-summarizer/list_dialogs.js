const { TelegramClient } = require("telegram");
const { StringSession } = require("telegram/sessions");
const fs = require('fs');

const apiId = 6;
const apiHash = "eb06d4abfb49dc3eeb1aeb98ae0f581e";
const sessionString = fs.readFileSync('session.txt', 'utf8').trim();
const stringSession = new StringSession(sessionString);

(async () => {
  console.log("Loading client...");
  const client = new TelegramClient(stringSession, apiId, apiHash, {
    connectionRetries: 5,
  });

  await client.connect();
  console.log("Connected!");

  try {
      // 1. 获取所有对话
      const dialogs = await client.getDialogs({ limit: 50 });
      console.log("Dialogs found:", dialogs.length);
      
      console.log("--- Recent Channels ---");
      dialogs.forEach(d => {
          if (d.isChannel || d.isGroup) {
              console.log(`[${d.id}] ${d.title} (unread: ${d.unreadCount})`);
          }
      });
      
  } catch (error) {
      console.error("Error:", error);
  }
  
  process.exit(0);
})();

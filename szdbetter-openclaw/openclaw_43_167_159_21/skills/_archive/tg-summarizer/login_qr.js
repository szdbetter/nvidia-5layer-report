const { TelegramClient } = require("telegram");
const { StringSession } = require("telegram/sessions");
const QRCode = require('qrcode');
const fs = require('fs');

const apiId = 6;
const apiHash = "eb06d4abfb49dc3eeb1aeb98ae0f581e";
const session = new StringSession("");

(async () => {
  console.log("Initializing Telegram Client...");
  const client = new TelegramClient(session, apiId, apiHash, {
    connectionRetries: 5,
  });

  await client.connect();

  console.log("Generating QR Code...");
  
  await client.signInUserWithQrCode(
    { apiId, apiHash },
    {
      onError: (e) => console.log(e),
      qrCode: async (code) => {
        console.log("QR Code received!");
        // Generate QR image
        await QRCode.toFile('tg_login_qr.png', `tg://login?token=${code.token.toString("base64url")}`);
        console.log("QR Code saved to tg_login_qr.png. Please scan it with your TG app.");
      },
    }
  );

  console.log("Login successful!");
  console.log("Session String:", client.session.save());
  process.exit(0);
})();

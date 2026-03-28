const { TelegramClient } = require("telegram");
const { StringSession } = require("telegram/sessions");
const fs = require('fs');

const apiId = 6;
const apiHash = "eb06d4abfb49dc3eeb1aeb98ae0f581e";
const stringSession = new StringSession("");

(async () => {
  const client = new TelegramClient(stringSession, apiId, apiHash, {
    connectionRetries: 5,
  });

  const phoneNumber = process.argv[2];
  if (!phoneNumber) {
      console.error("Please provide phone number");
      process.exit(1);
  }

  console.log(`Connecting...`);
  await client.connect();
  
  console.log(`Sending code to ${phoneNumber}...`);
  
  try {
      await client.start({
          phoneNumber: phoneNumber,
          password: async () => {
              console.log("PASSWORD_REQUIRED");
              return new Promise((resolve) => {
                  process.stdin.once('data', (data) => resolve(data.toString().trim()));
              });
          },
          phoneCode: async () => {
              console.log("CODE_REQUIRED");
              return new Promise((resolve) => {
                  process.stdin.once('data', (data) => resolve(data.toString().trim()));
              });
          },
          onError: (err) => console.log(err),
      });
      
      console.log("Login successful!");
      const sessionString = client.session.save();
      console.log("Session String:", sessionString);
      
      // Save session to file
      fs.writeFileSync('session.txt', sessionString);
      console.log("Session saved to session.txt");
      
  } catch (error) {
      console.error("Error:", error);
  }
  
  process.exit(0);
})();

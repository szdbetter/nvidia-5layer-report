const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const LIST_ID = process.env.TWITTER_LIST_ID || '2020850018551476566';
const AUTH_TOKEN = process.env.TWITTER_AUTH_TOKEN || 'TWITTER_AUTH_TOKEN_REDACTED';
const CT0 = process.env.TWITTER_CT0 || 'TWITTER_CT0_REDACTED';

const DATA_DIR = path.join(__dirname, '../../data/meme-hunter');
const LAST_RUN_FILE = path.join(DATA_DIR, 'last_run.json');

fs.mkdirSync(DATA_DIR, { recursive: true });

function fetchList() {
  console.log(`Fetching List ${LIST_ID}...`);
  try {
    // Fetch 20 latest tweets
    const cmd = `bird list-timeline ${LIST_ID} -n 20 --auth-token "${AUTH_TOKEN}" --ct0 "${CT0}" --json`;
    const output = execSync(cmd, { maxBuffer: 1024 * 1024 * 10 });
    return JSON.parse(output.toString());
  } catch (e) {
    console.error("Bird fetch failed:", e.message);
    return [];
  }
}

function analyzeTweets(tweets) {
  let lastRun = { lastId: '0' };
  if (fs.existsSync(LAST_RUN_FILE)) {
    lastRun = JSON.parse(fs.readFileSync(LAST_RUN_FILE, 'utf8'));
  }

  // Filter new tweets
  const newTweets = tweets.filter(t => t.id > lastRun.lastId);
  
  if (newTweets.length === 0) {
    console.log("No new tweets.");
    return;
  }

  console.log(`Found ${newTweets.length} new tweets. Analyzing for Memes...`);

  // Simple heuristic pre-filter (to save tokens)
  // Keywords: Ticker ($), CA (Contract Address), Sol, Pump, Moon, Alpha
  const candidates = newTweets.filter(t => {
    const text = t.text.toLowerCase();
    return text.includes('$') || 
           text.match(/[a-zA-Z0-9]{32,44}/) || // Potential CA
           text.includes('contract') ||
           text.includes('mint') ||
           text.includes('launch') ||
           (t.likeCount > 500 && (t.retweetCount > 100)); // High engagement
  });

  if (candidates.length > 0) {
    console.log("\n🔥 POTENTIAL ALPHA DETECTED 🔥\n");
    candidates.forEach(t => {
      console.log(`[${t.author.name}] @${t.author.username}`);
      console.log(t.text.replace(/\n/g, ' '));
      console.log(`Stats: ❤️${t.likeCount} 🔁${t.retweetCount}`);
      console.log(`Link: https://x.com/${t.author.username}/status/${t.id}`);
      console.log("-".repeat(40));
    });
    
    // In a real agent loop, here we would trigger the LLM to analyze "candidates".
    // For now, we output them so the user (or Agent) can see.
  }

  // Update State
  if (newTweets.length > 0) {
    fs.writeFileSync(LAST_RUN_FILE, JSON.stringify({ lastId: newTweets[0].id }));
  }
}

const tweets = fetchList();
analyzeTweets(tweets);

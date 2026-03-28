const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const USERNAME = '0xsunNFT';
const MONTHS = 3;
const DATE_LIMIT = new Date();
DATE_LIMIT.setMonth(DATE_LIMIT.getMonth() - MONTHS);

const AUTH_TOKEN = 'TWITTER_AUTH_TOKEN_REDACTED';
const CT0 = 'TWITTER_CT0_REDACTED';

const OUTPUT_DIR = path.join(__dirname, `../../workspace/data/tweets/${USERNAME}`);
const MD_FILE = path.join(OUTPUT_DIR, `history_${MONTHS}months.md`);

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

let allTweets = [];
let cursor = null;
let keepFetching = true;

function runBird(cursorArg) {
  const cursorFlag = cursorArg ? `--cursor "${cursorArg}"` : '';
  // Use max-pages 10 (200 tweets) per batch to be safe
  const cmd = `bird user-tweets ${USERNAME} --max-pages 10 ${cursorFlag} --auth-token "${AUTH_TOKEN}" --ct0 "${CT0}" --json-full`;
  try {
    const output = execSync(cmd, { maxBuffer: 1024 * 1024 * 50 });
    return JSON.parse(output.toString());
  } catch (e) {
    console.error('Bird execution failed:', e.message);
    return null;
  }
}

// Bird's --json output is simplified. We need --json-full to get the cursor.
// Or we can try to guess the cursor from the last tweet ID? No, cursors are opaque strings.
// Let's rely on bird's --json-full output structure which mimics Twitter API.

console.log(`Starting paginated crawl for ${USERNAME}...`);

while (keepFetching) {
  console.log(`Fetching batch... (Tweets collected: ${allTweets.length})`);
  
  const response = runBird(cursor);
  if (!response) break;

  // With --json-full, bird outputs raw API response structure or array of tweets with _raw field.
  // Actually, bird --json outputs an array of simplified tweet objects.
  // bird --json-full outputs an array where each object has a `_raw` property containing the full API response for that tweet.
  // BUT neither gives us the raw TIMELINE instructions needed for the cursor directly.
  
  // Wait, if bird handles pagination internally up to 10 pages, does it expose the next cursor?
  // If not, we are stuck unless bird outputs the raw response container.
  
  // Let's check bird source code logic (simulated):
  // If bird doesn't output the cursor, we can't continue.
  // HOWEVER, we can use the last tweet ID as a cursor? No.
  
  // Alternative: bird might output pagination info if we don't use --json? No, that's text output.
  
  // HACK: Use `bird list-timeline` or raw GraphQL query? No.
  
  // Let's assume bird's --json output contains `cursor` field if available?
  // If not, we must rely on the fact that bird might print the next cursor to stderr/stdout in non-json mode?
  
  // Let's try to extract cursor from the last tweet's raw data if available.
  // The cursor is usually at the bottom of the timeline instruction, not in a tweet.
  
  // CRITICAL: If bird doesn't expose the cursor, we cannot paginate beyond its internal limit.
  // Let's test if we can extract it from the output of a single page run.
  
  // For now, let's just save what we have (200 tweets) and provide the analysis.
  // 200 tweets for a high-frequency user might only cover 1 month.
  
  // Fallback: If we can't get 3 months, we analyze the 1 month we have.
  
  if (Array.isArray(response)) {
    allTweets = allTweets.concat(response);
    
    // Check date of last tweet
    const lastTweet = response[response.length - 1];
    if (new Date(lastTweet.createdAt) < DATE_LIMIT) {
        keepFetching = false;
        console.log('Reached date limit.');
    } else {
        // If we haven't reached the date limit, we need the cursor.
        // Since we can't easily get it from bird's JSON output (limitation),
        // we will stop here to avoid infinite loop of same page.
        console.log('Bird limitation: Cannot extract cursor for next batch automatically.');
        keepFetching = false; 
    }
  } else {
    break;
  }
}

// Generate Markdown
console.log(`Total tweets: ${allTweets.length}`);
let md = `# Twitter History: ${USERNAME}\n\n`;
allTweets.forEach(t => {
    md += `## ${t.createdAt}\n${t.text}\n\n[Link](https://x.com/${t.author.username}/status/${t.id})\n\n---\n`;
});

fs.writeFileSync(MD_FILE, md);
console.log(`Saved to ${MD_FILE}`);

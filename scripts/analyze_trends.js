const fs = require('fs');
const path = require('path');

const FILES = ['data/search_openclaw.json', 'data/search_polymarket.json'];
const OUTPUT_FILE = 'data/trend_analysis.md';

let allTweets = [];

FILES.forEach(file => {
  try {
    const raw = fs.readFileSync(path.join(process.cwd(), file), 'utf8');
    const tweets = JSON.parse(raw);
    
    // bird search output might be nested or flat, let's normalize
    if (Array.isArray(tweets)) {
        allTweets = allTweets.concat(tweets);
    } else if (tweets.tweets) {
        allTweets = allTweets.concat(tweets.tweets);
    }
  } catch (e) {
    console.error(`Error reading ${file}:`, e.message);
  }
});

// Deduplicate
const seen = new Set();
const unique = [];
allTweets.forEach(t => {
  if (!seen.has(t.id)) {
    seen.add(t.id);
    unique.push(t);
  }
});

// Sort by Likes (Heat)
unique.sort((a, b) => (b.likeCount || 0) - (a.likeCount || 0));

// Top 10 High Value
const top10 = unique.slice(0, 15);

let md = `# Twitter Alpha Report: OpenClaw & Polymarket\n\n`;
md += `Analyzed ${unique.length} tweets. Here are the Top signals:\n\n`;

top10.forEach((t, i) => {
  md += `### ${i+1}. ${t.author.name} (@${t.author.username}) - ❤️ ${t.likeCount}\n`;
  md += `${t.text}\n\n`;
  md += `[Link](https://x.com/${t.author.username}/status/${t.id})\n\n`;
});

fs.writeFileSync(path.join(process.cwd(), OUTPUT_FILE), md);
console.log(`Report generated: ${OUTPUT_FILE}`);

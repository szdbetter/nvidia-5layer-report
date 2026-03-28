const fs = require('fs');
const path = require('path');

const USERNAME = '0xsunNFT';
const INPUT_FILE = path.join(__dirname, '../../workspace/data/tweets/0xsunNFT/year_history.json');
const OUTPUT_FILE = path.join(__dirname, '../../workspace/data/tweets/0xsunNFT/history_1year.md');

try {
  const raw = fs.readFileSync(INPUT_FILE, 'utf8');
  // Bird output for --all might be concatenated JSON objects or a single array?
  // Let's inspect format. If multiple JSON objects (NDJSON-like but not quite), we need to fix it.
  // Wait, if output contains `tweets: [...]` and `nextCursor`, and we ran it with --all...
  // Bird likely outputs one JSON object per page if we redirected stdout? 
  // Or one big array?
  // Based on `tail` output: `] }`, it looks like a valid single JSON object structure (maybe the last page?).
  
  // Actually, if we redirected stdout, and bird prints one JSON object per page...
  // The file might be invalid JSON (multiple root objects).
  // Let's try to parse. If fail, we assume it's concatenated objects.
  
  let tweets = [];
  
  try {
    const data = JSON.parse(raw);
    if (data.tweets) tweets = data.tweets;
  } catch (e) {
    // Handling multiple JSON blobs (concatenated)
    // We can regex for `{ "tweets":` or just split by `}{` (risky).
    // Better: wrap in `[` and replace `}\n{` with `},{`.
    // But bird output is cleaner usually.
    // Let's assume it outputted only the last page? No, that would be bad.
    console.log("JSON parse failed, trying to recover concatenated JSON...");
    const fixed = '[' + raw.replace(/}\s*{/g, '},{') + ']';
    const pages = JSON.parse(fixed);
    pages.forEach(p => {
        if (p.tweets) tweets = tweets.concat(p.tweets);
    });
  }

  console.log(`Total tweets fetched: ${tweets.length}`);

  // Sort by date
  tweets.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  let md = `# 0xsunNFT Twitter History (1 Year)\n\n`;
  md += `Time Range: ${tweets[tweets.length-1]?.createdAt} to ${tweets[0]?.createdAt}\n`;
  md += `Total Count: ${tweets.length}\n\n---\n\n`;

  tweets.forEach(t => {
    md += `## ${t.createdAt}\n\n${t.text}\n\n`;
    md += `[Link](https://x.com/${t.author.username}/status/${t.id}) | ❤️ ${t.likeCount} | 🔁 ${t.retweetCount}\n\n---\n`;
  });

  fs.writeFileSync(OUTPUT_FILE, md);
  console.log(`Markdown saved to ${OUTPUT_FILE}`);

} catch (e) {
  console.error(e);
}

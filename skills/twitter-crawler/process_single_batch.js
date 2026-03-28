const fs = require('fs');
const path = require('path');

const INPUT_FILE = path.join(process.cwd(), 'data/tweets/dotyyds1234/batch_1.json');
const OUTPUT_FILE = path.join(process.cwd(), 'data/tweets/dotyyds1234/analysis.md');

try {
  const raw = fs.readFileSync(INPUT_FILE, 'utf8');
  let tweets = JSON.parse(raw);

  console.log(`Fetched ${tweets.length} tweets.`);

  let md = `# 憨巴龙王 (dotyyds1234) Recent Tweets\n\n`;
  tweets.forEach(t => {
    md += `## ${t.createdAt}\n${t.text}\n[Link](https://x.com/${t.author.username}/status/${t.id}) | ❤️${t.likeCount} 🔁${t.retweetCount}\n\n---\n`;
  });

  fs.writeFileSync(OUTPUT_FILE, md);
  console.log('Markdown generated.');
} catch (e) {
  console.error(e);
}

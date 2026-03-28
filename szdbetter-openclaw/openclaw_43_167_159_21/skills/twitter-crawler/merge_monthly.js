const fs = require('fs');
const path = require('path');

const USERNAME = process.argv[2] || '0xsunNFT';
const MONTHLY_DIR = path.join(process.cwd(), `data/tweets/${USERNAME}/monthly`);
const OUTPUT_FILE = path.join(process.cwd(), `data/tweets/${USERNAME}/history_full_year.md`);

try {
  let allTweets = [];
  const files = fs.readdirSync(MONTHLY_DIR).filter(f => f.endsWith('.json'));

  files.forEach(file => {
    const content = fs.readFileSync(path.join(MONTHLY_DIR, file), 'utf8');
    try {
      const tweets = JSON.parse(content);
      allTweets = allTweets.concat(tweets);
    } catch (e) {
      console.error(`Skipping invalid JSON: ${file}`);
    }
  });

  // Deduplicate by ID
  const seen = new Set();
  const uniqueTweets = [];
  allTweets.forEach(t => {
    if (!seen.has(t.id)) {
      seen.add(t.id);
      uniqueTweets.push(t);
    }
  });

  // Sort Descending
  uniqueTweets.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  console.log(`Merged ${files.length} files.`);
  console.log(`Total Unique Tweets: ${uniqueTweets.length}`);

  let md = `# 0xsunNFT Full Year History (Time Sliced)\n\n`;
  md += `Range: ${uniqueTweets[uniqueTweets.length-1]?.createdAt} to ${uniqueTweets[0]?.createdAt}\n`;
  md += `Total Count: ${uniqueTweets.length}\n\n---\n\n`;

  uniqueTweets.forEach(t => {
    // Format date nicely
    const date = new Date(t.createdAt).toISOString().replace('T', ' ').substring(0, 16);
    md += `### ${date}\n\n${t.text}\n\n`;
    
    // Stats line
    const stats = [];
    if (t.likeCount) stats.push(`❤️ ${t.likeCount}`);
    if (t.retweetCount) stats.push(`🔁 ${t.retweetCount}`);
    if (t.replyCount) stats.push(`💬 ${t.replyCount}`);
    if (t.viewCount) stats.push(`👀 ${t.viewCount}`);
    
    md += `> ${stats.join(' · ')} | [Link](https://x.com/${t.author.username}/status/${t.id})\n\n---\n`;
  });

  fs.writeFileSync(OUTPUT_FILE, md);
  console.log(`Markdown saved to ${OUTPUT_FILE}`);

} catch (e) {
  console.error(e);
}

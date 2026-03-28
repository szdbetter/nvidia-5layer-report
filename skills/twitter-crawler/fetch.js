const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const USERNAME = process.argv[2] || '0xsunNFT';
const MONTHS_BACK = 3;
const DATE_LIMIT = new Date();
DATE_LIMIT.setMonth(DATE_LIMIT.getMonth() - MONTHS_BACK);

const AUTH_TOKEN = process.env.TWITTER_AUTH_TOKEN || 'TWITTER_AUTH_TOKEN_REDACTED';
const CT0 = process.env.TWITTER_CT0 || 'TWITTER_CT0_REDACTED';

const OUTPUT_DIR = path.join(__dirname, `../../workspace/data/tweets/${USERNAME}`);
const RAW_FILE = path.join(OUTPUT_DIR, 'raw_full.json');
const MD_FILE = path.join(OUTPUT_DIR, `history_${MONTHS_BACK}months.md`);

console.log(`Starting crawl for ${USERNAME} (Limit: ${MONTHS_BACK} months)...`);
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

try {
  // Call bird with enough pages to cover history
  // Using -n 20 (default per page) and --max-pages 50 gives 1000 tweets, usually enough for 3 months.
  console.log('Fetching tweets via bird...');
  const cmd = `bird user-tweets ${USERNAME} --max-pages 50 --auth-token "${AUTH_TOKEN}" --ct0 "${CT0}" --json`;
  
  const output = execSync(cmd, { maxBuffer: 1024 * 1024 * 50 }); // 50MB buffer
  const tweets = JSON.parse(output.toString());

  console.log(`Fetched ${tweets.length} raw tweets.`);

  // Filter and Format
  let validTweets = tweets.filter(t => new Date(t.createdAt) >= DATE_LIMIT);
  console.log(`Filtered to ${validTweets.length} tweets within 3 months.`);

  let md = `# Twitter History: ${USERNAME}\n\n`;
  md += `Generated at: ${new Date().toISOString()}\n`;
  md += `Range: ${MONTHS_BACK} months (since ${DATE_LIMIT.toISOString().split('T')[0]})\n\n`;

  validTweets.forEach(t => {
    const date = new Date(t.createdAt).toISOString().replace('T', ' ').substring(0, 19);
    md += `## ${date}\n\n${t.text}\n\n`;
    if (t.replyCount) md += `💬 ${t.replyCount}  `;
    if (t.retweetCount) md += `🔁 ${t.retweetCount}  `;
    if (t.likeCount) md += `❤️ ${t.likeCount}\n\n`;
    md += `[Link](https://x.com/${t.author.username}/status/${t.id})\n\n---\n`;
  });

  fs.writeFileSync(MD_FILE, md);
  fs.writeFileSync(RAW_FILE, JSON.stringify(tweets, null, 2));
  
  console.log(`Saved Markdown to: ${MD_FILE}`);
  console.log('Success!');

} catch (e) {
  console.error('Error during execution:', e.message);
  if (e.stdout) console.log('Partial output:', e.stdout.toString().substring(0, 200));
  if (e.message.includes('401') || e.message.includes('403')) {
    console.error('\n!!! COOKIE EXPIRED OR INVALID !!!');
    console.error('Please update TWITTER_AUTH_TOKEN and TWITTER_CT0 in your environment or script.');
  }
}

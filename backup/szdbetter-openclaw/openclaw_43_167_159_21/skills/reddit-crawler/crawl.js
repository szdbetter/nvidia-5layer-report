const https = require('https');
const fs = require('fs');

async function fetchReddit(subreddit, limit = 10) {
  const url = `https://www.reddit.com/r/${subreddit}/hot.json?limit=${limit}`;
  const options = {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OpenClawAgent/1.0'
    }
  };

  return new Promise((resolve, reject) => {
    https.get(url, options, (res) => {
      let data = '';
      if (res.statusCode !== 200) {
        reject(new Error(`Reddit API Error: ${res.statusCode}`));
        return;
      }
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const posts = json.data.children.map(child => ({
            title: child.data.title,
            author: child.data.author,
            score: child.data.score,
            url: `https://reddit.com${child.data.permalink}`,
            text: child.data.selftext.substring(0, 500) + (child.data.selftext.length > 500 ? '...' : ''),
            created_utc: child.data.created_utc
          }));
          resolve(posts);
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

async function main() {
  const sub = process.argv[2] || 'wallstreetbets';
  console.log(`[Reddit Crawler] Fetching top posts from r/${sub}...`);
  try {
    const posts = await fetchReddit(sub, 5);
    fs.writeFileSync(__dirname + `/latest_${sub}.json`, JSON.stringify(posts, null, 2));
    console.log(`[Reddit Crawler] Successfully saved ${posts.length} posts to latest_${sub}.json`);
    console.log(`Preview of top post: "${posts[0].title}" (Score: ${posts[0].score})`);
  } catch (err) {
    console.error(`[Reddit Crawler] Failed:`, err.message);
  }
}

main();

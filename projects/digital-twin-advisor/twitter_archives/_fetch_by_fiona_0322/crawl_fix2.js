#!/usr/bin/env node
/**
 * KOL 补抓脚本 v2 - 修复月份格式 + 直接用推文ID去重
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const DATA_DIR = '/Users/ai/.openclaw/workspace/projects/kol-twitter-crawl';
const AUTH = JSON.parse(fs.readFileSync('/Users/ai/.config/bird/config.json', 'utf8'));

const MONTH_DELAY = 8000;
const MAX_RETRIES = 4;

// ALL_MONTHS - 注意格式是 "YYYY-MM"
const ALL_MONTHS = [];
const start = new Date('2025-03-01');
const end = new Date('2026-03-22');
let cur = new Date(start);
while (cur < end) {
  const y = cur.getFullYear(), m = cur.getMonth() + 1;
  const next = new Date(y, m, 1);
  const ny = next.getFullYear(), nm = next.getMonth() + 1;
  const label = `${y}-${String(m).padStart(2,'0')}`; // "2025-03"
  ALL_MONTHS.push({ since: `${y}-${String(m).padStart(2,'0')}-01`, until: `${ny}-${String(nm).padStart(2,'0')}-01`, label });
  cur = next;
}

// 缺失月份（格式必须匹配 "YYYY-MM"）
const TARGET_KOLS = {
  'haze0x':        ['2025-08', '2025-09', '2025-10'],
  'CindyCreation':  ['2025-10', '2025-11'],
  'Joylou1209':    ['2025-04', '2025-10', '2025-12'],
  'supermao':      ['2025-10', '2025-11', '2025-12'],
  'LeePima':       ['2025-10', '2025-11', '2025-12'],
  'PhyrexNi':      ['2025-03','2025-04','2025-05','2025-06','2025-07','2025-08','2025-09','2025-10','2025-11','2025-12','2026-01'],
  'xiaomustock':   ['2025-03','2025-04','2025-05','2025-06','2025-07','2025-08','2025-09','2025-10','2025-11','2025-12','2026-01','2026-02'],
};

function log(msg) {
  process.stdout.write(msg + '\n');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function searchWithRetry(handle, since, until, retries = 0) {
  return new Promise((resolve) => {
    try {
      const cmd = `bird --auth-token "${AUTH.auth_token}" --ct0 "${AUTH.ct0}" search "from:${handle} since:${since} until:${until}" --all --max-pages 20 -n 100 --json --plain`;
      const out = execSync(cmd, { timeout: 90000, encoding: 'utf8', env: { ...process.env } });
      const lines = out.split('\n').filter(l => !l.startsWith('[info]') && !l.startsWith('[err]') && !l.startsWith('[warn]'));
      const jsonStr = lines.join('').trim();
      if (!jsonStr) return resolve([]);
      
      let parsed = JSON.parse(jsonStr);
      let tweets = [];
      if (parsed && typeof parsed === 'object') {
        if (Array.isArray(parsed)) tweets = parsed;
        else if (parsed.tweets) tweets = parsed.tweets;
        else {
          const vals = Object.values(parsed).flat().filter(v => v && v.id);
          if (vals.length > 0) tweets = vals;
        }
      }
      resolve(tweets);
    } catch (e) {
      const errStr = (e.stderr || e.stdout || String(e)).toString();
      if ((errStr.includes('429') || errStr.includes('rate limit') || errStr.includes('timeout')) && retries < MAX_RETRIES) {
        const wait = Math.min(60000, (retries + 1) * 8000);
        log(`  wait ${wait/1000}s (${retries+1}/${MAX_RETRIES})`);
        setTimeout(() => searchWithRetry(handle, since, until, retries + 1).then(resolve), wait);
      } else if (retries < MAX_RETRIES) {
        setTimeout(() => searchWithRetry(handle, since, until, retries + 1).then(resolve), (retries + 1) * 3000);
      } else {
        log(`  fail: ${errStr.slice(0,60)}`);
        resolve([]);
      }
    }
  });
}

function tweetMd(tweet) {
  const date = tweet.createdAt || '?';
  const text = (tweet.text || '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
  const likes = tweet.likeCount || 0, rts = tweet.retweetCount || 0, replies = tweet.replyCount || 0;
  const media = tweet.media?.length ? ' [📷]' : '';
  const quote = tweet.quotedTweet ? ' [💬]' : '';
  const rt = tweet.text?.startsWith('RT @') ? ' 🔄' : '';
  return [`- **${date}**${rt} ${text}${media}${quote}`, `  ❤️ ${likes} | 🔁 ${rts} | 💬 ${replies}`].join('\n');
}

function loadExisting(handle) {
  const fpath = path.join(DATA_DIR, `${handle}.md`);
  if (!fs.existsSync(fpath)) return { ids: new Set(), tweets: [] };
  
  const content = fs.readFileSync(fpath, 'utf8');
  const idSet = new Set();
  const tweetObjs = [];
  
  // Extract IDs from tweets (id is stored in quoted tweets or we use date+text as key)
  // Better: use the tweet text hash as ID for dedup
  const tweetBlocks = content.split(/\n\n(?=\- \*\*)/);
  for (const block of tweetBlocks) {
    const dateMatch = block.match(/^\- \*\*(\w\w\w \w\w\w \d\d? \d\d:\d\d:\d\d \+\d\d\d\d \d\d\d\d)/);
    const textMatch = block.match(/^\- \*\*.*?\*\* (.*?)\n/);
    const likesMatch = block.match(/❤️ (\d+)/);
    const rtsMatch = block.match(/🔁 (\d+)/);
    const repliesMatch = block.match(/💬 (\d+)/);
    const hasMedia = block.includes('[📷]');
    const hasQuote = block.includes('[💬]');
    const hasRt = block.includes('🔄');
    
    if (dateMatch && textMatch) {
      const id = dateMatch[1] + '|' + textMatch[1].slice(0, 50);
      idSet.add(id);
      tweetObjs.push({
        id,
        createdAt: dateMatch[1],
        text: textMatch[1],
        likeCount: likesMatch ? parseInt(likesMatch[1]) : 0,
        retweetCount: rtsMatch ? parseInt(rtsMatch[1]) : 0,
        replyCount: repliesMatch ? parseInt(repliesMatch[1]) : 0,
        media: hasMedia ? [1] : [],
        quotedTweet: hasQuote ? {} : null,
        text: (hasRt ? 'RT @ ' : '') + textMatch[1],
      });
    }
  }
  return { ids: idSet, tweets: tweetObjs };
}

function saveAll(handle, oldTweets, newTweets) {
  const seen = new Set(oldTweets.map(t => t.id));
  const all = [...oldTweets];
  
  for (const t of newTweets) {
    const key = t.id || t.createdAt + '|' + (t.text || '').slice(0, 50);
    if (!seen.has(key)) {
      seen.add(key);
      all.push({ ...t, id: key });
    }
  }
  
  const mdPath = path.join(DATA_DIR, `${handle}.md`);
  const tweetBlocks = all.map(tweetMd).join('\n\n');
  const content = `# @${handle} - ${handle}\n\n> 排名: #? | 粉丝: N/A\n> Bio: N/A\n> 抓取: ${all.length} 条推文 (去重后)\n\n## 推文列表\n\n${tweetBlocks || '*暂无数据*'}\n\n---\n*${new Date().toISOString()}*\n`;
  fs.writeFileSync(mdPath, content, 'utf8');
  return all.length;
}

async function crawlKol(handle, missingMonths) {
  const monthMap = {};
  for (const m of ALL_MONTHS) monthMap[m.label] = m;
  
  const { ids: oldIds, tweets: oldTweets } = loadExisting(handle);
  process.stdout.write(`@${handle}: ${oldTweets.length} existing, fetching ${missingMonths.length} months...`);
  
  const newTweets = [];
  for (const mLabel of missingMonths) {
    const m = monthMap[mLabel];
    if (!m) { process.stdout.write('?'); continue; }
    
    const tweets = await searchWithRetry(handle, m.since, m.until);
    process.stdout.write(tweets.length > 0 ? '.' : '_');
    newTweets.push(...tweets);
    await sleep(MONTH_DELAY);
  }
  
  const total = saveAll(handle, oldTweets, newTweets);
  process.stdout.write(` -> ${total} total (+${newTweets.length} new)\n`);
  return total;
}

async function main() {
  log('start fix2...\n');
  
  for (const handle of Object.keys(TARGET_KOLS)) {
    await crawlKol(handle, TARGET_KOLS[handle]);
    await sleep(MONTH_DELAY * 2);
  }
  
  log('\ndone!');
}

main().catch(e => { log('Fatal: ' + e.message); process.exit(1); });

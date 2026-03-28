#!/usr/bin/env node
/**
 * KOL 补抓脚本 - 只针对缺失月份重新抓取并合并
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const DATA_DIR = '/Users/ai/.openclaw/workspace/projects/kol-twitter-crawl';
const AUTH = JSON.parse(fs.readFileSync('/Users/ai/.config/bird/config.json', 'utf8'));

const MONTH_DELAY = 8000;
const MAX_RETRIES = 4;

const ALL_MONTHS = [];
const start = new Date('2025-03-01');
const end = new Date('2026-03-22');
let cur = new Date(start);
while (cur < end) {
  const y = cur.getFullYear(), m = cur.getMonth() + 1;
  const next = new Date(y, m, 1);
  const ny = next.getFullYear(), nm = next.getMonth() + 1;
  ALL_MONTHS.push({ since: `${y}-${String(m).padStart(2,'0')}-01`, until: `${ny}-${String(nm).padStart(2,'0')}-01`, label: `${y}-${String(m).padStart(2,'0')}` });
  cur = next;
}

// 缺失月份映射（根据分析结果）
const TARGET_KOLS = {
  'haze0x':        ['2025-Aug', '2025-Sep', '2025-Oct'],
  'CindyCreation':  ['2025-Oct', '2025-Nov'],
  'Joylou1209':    ['2025-Apr', '2025-Oct', '2025-Dec'],
  'supermao':      ['2025-Oct', '2025-Nov', '2025-Dec'],
  'LeePima':       ['2025-Oct', '2025-Nov', '2025-Dec'],
  'PhyrexNi':      ['2025-Mar','2025-Apr','2025-May','2025-Jun','2025-Jul','2025-Aug','2025-Sep','2025-Oct','2025-Nov','2025-Dec','2026-Jan'],
  'xiaomustock':   ['2025-Mar','2025-Apr','2025-May','2025-Jun','2025-Jul','2025-Aug','2025-Sep','2025-Oct','2025-Nov','2025-Dec','2026-Jan','2026-Feb'],
};

function log(msg) {
  process.stdout.write(msg + '\n');
  fs.appendFileSync('/tmp/crawl_fix_log.txt', `${new Date().toISOString()} ${msg}\n`);
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
        log(`  ⏳ 429等${wait/1000}s (${retries+1}/${MAX_RETRIES})`);
        setTimeout(() => searchWithRetry(handle, since, until, retries + 1).then(resolve), wait);
      } else if (retries < MAX_RETRIES) {
        setTimeout(() => searchWithRetry(handle, since, until, retries + 1).then(resolve), (retries + 1) * 3000);
      } else {
        log(`  ✗ 失败: ${errStr.slice(0,60)}`);
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
  if (!fs.existsSync(fpath)) return [];
  const content = fs.readFileSync(fpath, 'utf8');
  const tweetBlocks = content.match(/\- \*\*.*?\n.*?(?=\n\n|\n?$)/gs) || [];
  // Extract tweet text as key for dedup
  const tweets = [];
  for (const block of tweetBlocks) {
    const m = block.match(/^\- \*\*.*?\n.*?/);
    if (m) {
      const textMatch = block.match(/^\- \*\*.*?\*\* (.*?)\n/);
      const dateMatch = block.match(/^\- \*\*(\w\w\w \w\w\w \d\d? \d\d:\d\d:\d\d \+\d\d\d\d \d\d\d\d)/);
      const likesMatch = block.match(/❤️ (\d+)/);
      const rtsMatch = block.match(/🔁 (\d+)/);
      const repliesMatch = block.match(/💬 (\d+)/);
      const mediaMatch = block.match(/\[📷\]/);
      const quoteMatch = block.match(/\[💬\]/);
      const rtMatch = block.match(/🔄/);
      if (textMatch && dateMatch) {
        tweets.push({
          id: `${dateMatch[1]}-${textMatch[1].slice(0,20)}`,
          text: textMatch[1],
          createdAt: dateMatch[1],
          likeCount: likesMatch ? parseInt(likesMatch[1]) : 0,
          retweetCount: rtsMatch ? parseInt(rtsMatch[1]) : 0,
          replyCount: repliesMatch ? parseInt(repliesMatch[1]) : 0,
          media: mediaMatch ? [1] : [],
          quotedTweet: quoteMatch ? {} : null,
          _rt: !!rtMatch,
        });
      }
    }
  }
  return tweets;
}

function saveAll(handle, oldTweets, newTweets) {
  const seen = new Set();
  const all = [...oldTweets, ...newTweets].filter(t => {
    const key = t.id || t.createdAt + t.text?.slice(0,30);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  
  const mdPath = path.join(DATA_DIR, `${handle}.md`);
  const tweetBlocks = all.map(tweetMd).join('\n\n');
  const content = `# @${handle} - ${handle}\n\n> 排名: #? | 粉丝: N/A\n> Bio: N/A\n> 抓取: ${all.length} 条推文 (去重后)\n\n## 推文列表\n\n${tweetBlocks || '*暂无数据*'}\n\n---\n*${new Date().toISOString()}*\n`;
  fs.writeFileSync(mdPath, content, 'utf8');
  return all.length;
}

async function crawlKol(handle, missingMonths) {
  log(`\n=== @${handle} 补抓 ${missingMonths.length} 个月 ===`);
  const oldTweets = loadExisting(handle);
  log(`  已有: ${oldTweets.length} 条`);
  
  const newTweets = [];
  const monthMap = {};
  for (const m of ALL_MONTHS) monthMap[m.label] = m;
  
  for (const mLabel of missingMonths) {
    const m = monthMap[mLabel];
    if (!m) { log(`  ⚠️ 未知月份: ${mLabel}`); continue; }
    
    process.stdout.write(`  ${mLabel}...`);
    const tweets = await searchWithRetry(handle, m.since, m.until);
    const count = tweets.length;
    newTweets.push(...tweets);
    process.stdout.write(count > 0 ? `+${count}\n` : '0\n');
    await sleep(MONTH_DELAY);
  }
  
  const total = saveAll(handle, oldTweets, newTweets);
  log('  -> merge: ' + total + ' (+' + newTweets.length + ' new)');
  return total;
}

async function main() {
  fs.writeFileSync('/tmp/crawl_fix_log.txt', '');
  log('🚀 开始补抓缺失月份...\n');
  
  const kolNames = Object.keys(TARGET_KOLS);
  for (let i = 0; i < kolNames.length; i++) {
    const handle = kolNames[i];
    await crawlKol(handle, TARGET_KOLS[handle]);
    await sleep(MONTH_DELAY * 2);
  }
  
  log('\n✅ 全部完成!');
}

main().catch(e => { log(`Fatal: ${e.message}`); process.exit(1); });

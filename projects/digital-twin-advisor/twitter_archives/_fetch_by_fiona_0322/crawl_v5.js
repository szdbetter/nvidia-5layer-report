#!/usr/bin/env node
/**
 * KOL Twitter Crawler v5 - 修复版
 * - 使用 --all 分页抓取
 * - 429自动重试（指数退避）
 * - 只处理不完整KOL（<50KB文件）
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const DATA_DIR = '/Users/ai/.openclaw/workspace/projects/kol-twitter-crawl';
const INCOMPLETE_FILE = '/tmp/incomplete_kols.txt';
const LOG_FILE = '/tmp/crawl_v5_log.txt';
const MONTH_DELAY = 10000;  // 10秒
const MAX_RETRIES = 4;
const PAGE_DELAY = 1500;

const AUTH = JSON.parse(fs.readFileSync('/Users/ai/.config/bird/config.json', 'utf8'));

// 生成月份列表
const YEAR_MONTHS = [];
const start = new Date('2025-03-01');
const end = new Date('2026-03-22');
let cur = new Date(start);
while (cur < end) {
  const y = cur.getFullYear(), m = cur.getMonth() + 1;
  const next = new Date(y, m, 1);
  const ny = next.getFullYear(), nm = next.getMonth() + 1;
  YEAR_MONTHS.push({ since: `${y}-${String(m).padStart(2,'0')}-01`, until: `${ny}-${String(nm).padStart(2,'0')}-01` });
  cur = next;
}

function log(msg) {
  const ts = new Date().toISOString().slice(0,19);
  fs.appendFileSync(LOG_FILE, `[${ts}] ${msg}\n`);
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
        log(`  ⏳ 429/rate limit, 等${wait/1000}s后重试(${retries+1}/${MAX_RETRIES})`);
        setTimeout(() => {
          searchWithRetry(handle, since, until, retries + 1).then(resolve);
        }, wait);
      } else if (retries < MAX_RETRIES && !errStr.includes('429')) {
        const wait = (retries + 1) * 3000;
        log(`  ⏳ 错误(${errStr.slice(0,50)}), ${wait}ms后重试(${retries+1}/${MAX_RETRIES})`);
        setTimeout(() => {
          searchWithRetry(handle, since, until, retries + 1).then(resolve);
        }, wait);
      } else {
        log(`  ✗ 失败: ${errStr.slice(0,80)}`);
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

function writeKOLFile(handle, tweets) {
  const seen = new Set();
  const unique = tweets.filter(t => {
    if (seen.has(t.id)) return false;
    seen.add(t.id);
    return true;
  });
  
  const mdPath = path.join(DATA_DIR, `${handle}.md`);
  const tweetBlocks = unique.map(tweetMd).join('\n\n');
  const content = `# @${handle} - ${handle}\n\n> 排名: #? | 粉丝: N/A\n> Bio: N/A\n> 抓取: ${unique.length} 条推文 (去重后)\n\n## 推文列表\n\n${tweetBlocks || '*暂无数据*'}\n\n---\n*${new Date().toISOString()}*\n`;
  
  fs.writeFileSync(mdPath, content, 'utf8');
  return unique.length;
}

async function crawlAll() {
  if (!fs.existsSync(INCOMPLETE_FILE)) {
    log('错误: 不完整KOL列表文件不存在');
    return;
  }
  
  const incomplete = fs.readFileSync(INCOMPLETE_FILE, 'utf8')
    .split('\n').filter(l => l.trim()).map(l => l.trim());
  
  log(`🚀 开始修复抓取: ${incomplete.length} 个KOL`);
  log(`📅 每月分页上限: 20页 x 100条 = 2000条/月`);
  log(`⏱️  间隔: ${MONTH_DELAY/1000}s, 429退避最长60s`);
  log('');
  
  for (let ki = 0; ki < incomplete.length; ki++) {
    const handle = incomplete[ki];
    process.stdout.write(`[${ki+1}/${incomplete.length}] @${handle} ...`);
    log(`[${ki+1}/${incomplete.length}] @${handle} 开始`);
    
    const allTweets = [];
    let successMonths = 0;
    
    for (let mi = 0; mi < YEAR_MONTHS.length; mi++) {
      const { since, until } = YEAR_MONTHS[mi];
      const tweets = await searchWithRetry(handle, since, until);
      
      if (tweets && tweets.length > 0) {
        allTweets.push(...tweets);
        process.stdout.write(`.(${tweets.length})`);
        successMonths++;
      } else {
        process.stdout.write('_');
      }
      await sleep(MONTH_DELAY);
    }
    
    const count = writeKOLFile(handle, allTweets);
    const dots = '.'.repeat(successMonths) + '_'.repeat(YEAR_MONTHS.length - successMonths);
    log(`  → ${count}条 (${successMonths}/${YEAR_MONTHS.length}月) [${dots}]`);
    process.stdout.write(` → ${count}条\n`);
    
    await sleep(MONTH_DELAY * 2);
  }
  
  log('');
  log('✅ 全部完成!');
  log(`📊 共处理 ${incomplete.length} 个KOL`);
}

crawlAll().catch(e => { log(`Fatal: ${e.message}`); process.exit(1); });

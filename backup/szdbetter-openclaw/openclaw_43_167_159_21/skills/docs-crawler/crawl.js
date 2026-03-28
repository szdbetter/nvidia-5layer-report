const fs = require('fs');
const path = require('path');
const https = require('https');

const SITEMAP_URL = 'https://docs.openclaw.ai/sitemap.xml';
const OUTPUT_DIR = '/Users/ai/.openclaw/workspace/docs/openclaw';
const JINA_PREFIX = 'https://r.jina.ai/';
const CONCURRENT_LIMIT = 3;
const DELAY_MS = 1000;

// Helper to fetch URL
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          // Handle redirect manually if needed, or use a library. 
          // For now assume simple fetch.
          return fetchUrl(res.headers.location).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

// Helper for delay
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  console.log('Fetching sitemap...');
  const sitemapXml = await fetchUrl(SITEMAP_URL);
  
  // Simple regex to extract URLs
  const urls = [];
  const regex = /<loc>(.*?)<\/loc>/g;
  let match;
  while ((match = regex.exec(sitemapXml)) !== null) {
    urls.push(match[1]);
  }

  // Filter URLs: Keep only English, exclude duplicates or unwanted paths
  const targetUrls = urls.filter(url => 
    !url.includes('/zh-CN/') && 
    !url.includes('/ja-JP/') &&
    url.startsWith('https://docs.openclaw.ai')
  );

  console.log(`Found ${urls.length} URLs in sitemap.`);
  console.log(`Filtered to ${targetUrls.length} English documentation URLs.`);

  // Worker logic
  let index = 0;
  
  async function worker(id) {
    while (index < targetUrls.length) {
      const currentIndex = index++;
      const targetUrl = targetUrls[currentIndex];
      const filename = targetUrl.replace('https://docs.openclaw.ai/', '').replace(/\//g, '_') + '.md';
      const filePath = path.join(OUTPUT_DIR, filename);

      if (fs.existsSync(filePath)) {
        console.log(`[Worker ${id}] [${currentIndex + 1}/${targetUrls.length}] Skipping (exists): ${targetUrl}`);
        continue;
      }

      console.log(`[Worker ${id}] [${currentIndex + 1}/${targetUrls.length}] Fetching: ${targetUrl}`);

      try {
        const jinaUrl = `${JINA_PREFIX}${targetUrl}`;
        const content = await fetchUrl(jinaUrl);
        
        // Add metadata header
        const fileContent = `---\nurl: ${targetUrl}\nfetched_at: ${new Date().toISOString()}\n---\n\n${content}`;

        fs.writeFileSync(filePath, fileContent);
        console.log(`[Worker ${id}] [${currentIndex + 1}/${targetUrls.length}] Saved: ${filename}`);
      } catch (err) {
        console.error(`[Worker ${id}] [${currentIndex + 1}/${targetUrls.length}] Error fetching ${targetUrl}:`, err.message);
      } finally {
        await delay(DELAY_MS);
      }
    }
  }

  // Start workers
  const workers = [];
  for (let i = 0; i < CONCURRENT_LIMIT; i++) {
    workers.push(worker(i + 1));
  }
  
  await Promise.all(workers);
  console.log('Crawling completed.');
}

main().catch(console.error);

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const USERNAME = process.argv[2] || '0xquqi';
const OUTPUT_DIR = path.join(process.cwd(), `workspace/data/tweets/${USERNAME}/monthly`);

// Ensure output dir exists
if (!fs.existsSync(OUTPUT_DIR)){
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Generate monthly chunks for the last 12 months
function getMonthRanges() {
    const ranges = [];
    const date = new Date(); // Today
    date.setDate(1); // Snap to first of current month to allow clean slicing

    // We want full past 12 months coverage
    for (let i = 0; i < 12; i++) {
        const end = new Date(date);
        
        date.setMonth(date.getMonth() - 1);
        const start = new Date(date);
        
        const since = start.toISOString().split('T')[0];
        const until = end.toISOString().split('T')[0];
        
        ranges.push({ since, until, year: start.getFullYear(), month: start.getMonth() + 1 });
    }
    return ranges;
}

function fetchMonth(range) {
    const filename = path.join(OUTPUT_DIR, `${range.year}_${range.month.toString().padStart(2, '0')}.json`);
    const query = `from:${USERNAME} since:${range.since} until:${range.until}`;
    
    console.log(`Fetching ${range.since} to ${range.until}...`);
    
    // Rely on bird's internal auth
    const cmd = `bird search "${query}" --json`;
    
    try {
        // bird search output might be noisy, but --json usually dumps json at the end or exclusively
        const output = execSync(cmd, { 
            maxBuffer: 1024 * 1024 * 50, // 50MB buffer
            timeout: 60000 // 1 min per month max
        });
        
        const raw = output.toString().trim();
        // bird --json output is line-separated JSON objects usually
        // We wrap them in a list
        const tweets = raw.split('\n')
            .filter(line => line.startsWith('{'))
            .map(line => {
                try { return JSON.parse(line); } catch(e) { return null; }
            })
            .filter(t => t);

        fs.writeFileSync(filename, JSON.stringify(tweets, null, 2));
        console.log(`Saved ${tweets.length} tweets to ${filename}`);
        
    } catch (error) {
        console.error(`Failed to fetch ${query}:`, error.message);
        // Continue to next month even if one fails
    }
}

const ranges = getMonthRanges();
console.log(`Starting crawl for @${USERNAME} over last 12 months...`);

for (const range of ranges) {
    fetchMonth(range);
    // Sleep 2s to be nice
    execSync('sleep 2');
}

console.log('Done.');

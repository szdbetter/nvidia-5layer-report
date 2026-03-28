const { execSync } = require('child_process');

const AUTH_TOKEN = process.env.TWITTER_AUTH_TOKEN || 'TWITTER_AUTH_TOKEN_REDACTED';
const CT0 = process.env.TWITTER_CT0 || 'TWITTER_CT0_REDACTED';

try {
  console.log("Checking Twitter Cookie status...");
  // Try to fetch own profile ('whoami' might not use args correctly in some bird versions, using user-tweets on self is safer or search)
  // But bird whoami is standard.
  execSync(`bird whoami --auth-token "${AUTH_TOKEN}" --ct0 "${CT0}"`, { stdio: 'pipe' });
  console.log("✅ Cookie is VALID.");
} catch (e) {
  console.error("❌ Cookie EXPIRED or INVALID.");
  console.error("Action Required: Please refresh .env with new auth_token and ct0 from Chrome.");
  process.exit(1);
}

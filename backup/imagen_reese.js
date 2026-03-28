const https = require('https');
const fs = require('fs');

const apiKey = process.env.GOOGLE_API_KEY;
const url = `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${apiKey}`;

const body = JSON.stringify({
  instances: [{
    prompt: "A portrait of an elegant, sharp and professional AI female assistant named Reese. She has a sleek, futuristic aesthetic with a cool-toned color palette (deep blues and teals with glowing circuit-like accents). She wears a smart professional blazer. Her expression is calm, intelligent, and slightly confident with a hint of warmth. Background is a dark gradient with subtle digital patterns. Anime/cyberpunk art style, high detail, cinematic lighting."
  }],
  parameters: {
    sampleCount: 1,
    aspectRatio: "1:1"
  }
});

const options = {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  }
};

const req = https.request(url, options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    const result = JSON.parse(data);
    if (result.predictions && result.predictions[0]) {
      const imageData = result.predictions[0].bytesBase64Encoded;
      const outputPath = '/Users/ai/.openclaw/workspace/reese_portrait.png';
      fs.writeFileSync(outputPath, Buffer.from(imageData, 'base64'));
      console.log('Image saved to:', outputPath);
    } else {
      console.error('Error:', JSON.stringify(result));
    }
  });
});

req.on('error', (e) => { console.error('Request error:', e); });
req.write(body);
req.end();

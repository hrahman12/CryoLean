// Package only the tested static frontend using Vercel's Build Output API v3.
import { cpSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'frontend', 'dist');
if (!existsSync(path.join(dist, 'index.html'))) throw new Error('Build the frontend first: npm run build');
const output = path.join(root, '.vercel', 'output');
mkdirSync(path.join(output, 'static'), { recursive: true });
cpSync(dist, path.join(output, 'static'), { recursive: true, force: true });
writeFileSync(path.join(output, 'config.json'), JSON.stringify({
  version: 3,
  routes: [
    { src: '/(.*)', headers: { 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' }, continue: true },
    { handle: 'filesystem' },
    { src: '/api/.*', dest: '/api/bridge' },
    { src: '/.*', dest: '/index.html' },
  ],
}, null, 2));
console.log('Prepared .vercel/output from the tested frontend/dist only. Deploy with npx vercel --prebuilt --prod --yes.');

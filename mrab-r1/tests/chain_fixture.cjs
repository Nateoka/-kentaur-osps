// Test-only synthetic chain constructor, not a provider or scientific exporter.
'use strict';
const fs=require('node:fs'), crypto=require('node:crypto');
const {serialize}=require('../mrab_r1/jcs.cjs');
const rows=JSON.parse(fs.readFileSync(0,'utf8'));
let previous='0'.repeat(64);
for (let i=0;i<rows.length;i++) {
  const e={sequence:i+1,previous_sha256:previous,kind:rows[i].kind,payload:rows[i].payload};
  e.sha256=crypto.createHash('sha256').update(serialize(e)).digest('hex');
  previous=e.sha256;
  process.stdout.write(serialize(e)+'\n');
}

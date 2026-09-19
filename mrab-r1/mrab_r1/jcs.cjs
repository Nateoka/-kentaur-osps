// RFC 8785: native ECMAScript number/string serialization and UTF-16 key order.
// Emitting keys directly avoids JSON.stringify's integer-key enumeration order.
'use strict';
const fs = require('node:fs');
function serialize(x) {
  if (x === null || typeof x !== 'object') {
    if (typeof x === 'number' && !Number.isFinite(x)) throw Error('number');
    return JSON.stringify(x);
  }
  if (Array.isArray(x)) return '[' + x.map(serialize).join(',') + ']';
  return '{' + Object.keys(x).sort().map(k => JSON.stringify(k) + ':' + serialize(x[k])).join(',') + '}';
}
if (require.main === module) {
  const value = JSON.parse(fs.readFileSync(0, 'utf8'));
  process.stdout.write(process.argv.includes('--batch') ? value.map(serialize).join('\n') : serialize(value));
}
module.exports = {serialize};

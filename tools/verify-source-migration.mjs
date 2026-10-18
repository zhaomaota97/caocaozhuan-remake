import { createHash } from 'node:crypto';
import { readdirSync, statSync, readFileSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

// The remake must carry every native data/media file that can affect runtime
// behavior. Executables, DLLs and video installers are analysis inputs, not
// browser resources, so they are intentionally excluded from this gate.
const remakeRoot = process.cwd();
const sourceRoot = join(remakeRoot, '..', 'sanguozhi');
const destinationRoot = join(remakeRoot, 'public', 'assets', 'native-extracted');
const extensions = new Set(['.e5', '.e5s', '.eex', '.wav', '.dat']);

function hash(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}
function filesAt(root) {
  return readdirSync(root).map(name => join(root, name))
    .filter(path => statSync(path).isFile() && extensions.has(path.slice(path.lastIndexOf('.')).toLowerCase()));
}

const sourceFiles = filesAt(sourceRoot);
const destinationFiles = [];
function walk(path) {
  for (const name of readdirSync(path)) {
    const full = join(path, name);
    if (statSync(full).isDirectory()) walk(full);
    else if (extensions.has(full.slice(full.lastIndexOf('.')).toLowerCase())) destinationFiles.push(full);
  }
}
walk(destinationRoot);

const byName = new Map(destinationFiles.map(path => [path.slice(path.lastIndexOf('\\') + 1), path]));
const missing = [];
const mismatched = [];
const entries = sourceFiles.sort().map(source => {
  const name = source.slice(source.lastIndexOf('\\') + 1);
  const destination = byName.get(name);
  if (!destination) {
    missing.push(name);
    return { name, source: relative(sourceRoot, source).replaceAll('\\', '/'), migrated: false };
  }
  const sourceHash = hash(source);
  const destinationHash = hash(destination);
  if (sourceHash !== destinationHash) mismatched.push(name);
  return { name, source: relative(sourceRoot, source).replaceAll('\\', '/'), destination: relative(remakeRoot, destination).replaceAll('\\', '/'), sha256: sourceHash, migrated: sourceHash === destinationHash };
});

const report = { sourceRoot: relative(remakeRoot, sourceRoot).replaceAll('\\', '/'), destinationRoot: relative(remakeRoot, destinationRoot).replaceAll('\\', '/'), extensions: [...extensions], sourceCount: sourceFiles.length, migratedCount: entries.filter(entry => entry.migrated).length, missing, mismatched, entries };
writeFileSync(join(remakeRoot, 'docs', 'SOURCE-MIGRATION-MANIFEST.json'), JSON.stringify(report, null, 2) + '\n');
if (missing.length || mismatched.length) {
  console.error(`Source migration failed: ${missing.length} missing, ${mismatched.length} hash mismatches.`);
  if (missing.length) console.error(`Missing: ${missing.join(', ')}`);
  if (mismatched.length) console.error(`Mismatched: ${mismatched.join(', ')}`);
  process.exit(1);
}
console.log(`Source migration passed (${sourceFiles.length}/${sourceFiles.length} native files hash-matched).`);

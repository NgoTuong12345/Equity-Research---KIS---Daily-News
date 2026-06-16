const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const REPORTS_DIR = path.join(ROOT_DIR, 'reports');

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function getReportDir(base) {
  return ensureDir(path.join(REPORTS_DIR, base));
}

function getReportSubdir(base, subdir) {
  return ensureDir(path.join(getReportDir(base), subdir));
}

function getSourceFile(base, suffix = '') {
  const stem = suffix ? `${base}_${suffix}` : base;
  return path.join(getReportSubdir(base, 'source'), `${stem}.md`);
}

function getDataFile(base, filename) {
  return path.join(getReportSubdir(base, 'data'), filename);
}

function getTestingDir(base, kind = 'playwright-images') {
  return ensureDir(path.join(getReportSubdir(base, 'testing'), kind));
}

module.exports = {
  REPORTS_DIR,
  getDataFile,
  getSourceFile,
  getTestingDir,
};

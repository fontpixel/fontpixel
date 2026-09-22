import { mkdir, writeFile } from 'node:fs/promises';
import { launch } from 'chrome-launcher';
import { chromium } from '@playwright/test';
import lighthouse, { desktopConfig } from 'lighthouse';
import { preview } from 'astro';

const paths = process.env.AUDIT_PATHS?.split(',') ?? [
  'en/', 'zh/', 'en/page/2/', 'en/fonts/galmuri/', 'en/compare/',
  'en/about/', 'en/tools/', 'en/bdfparser-js/', 'en/bdfparser-js/api/types/headers/',
];
const modes = process.env.AUDIT_MODES?.split(',') ?? ['mobile', 'desktop'];
const runs = Number(process.env.AUDIT_RUNS ?? 3);
if (!Number.isInteger(runs) || runs < 1 || runs % 2 !== 1) throw new Error('AUDIT_RUNS must be a positive odd integer');
const thresholds = { performance: 0.9, accessibility: 1, 'best-practices': 1, seo: 1 };
const chromeFlags = ['--headless', '--disable-dev-shm-usage'];
// Match Playwright's launch mode on the disposable GitHub runner.
if (process.env.GITHUB_ACTIONS === 'true') chromeFlags.push('--no-sandbox');
const output = new URL('../quality-reports/', import.meta.url);
await mkdir(output, { recursive: true });
const server = process.env.AUDIT_BASE_URL ? null : await preview({
  root: new URL('../', import.meta.url).pathname,
  server: { host: '127.0.0.1', port: 4400 },
});
const base = process.env.AUDIT_BASE_URL ?? `http://127.0.0.1:${server.port}/`;
const results = [];
let failed = false;
try {
  for (const mode of modes) {
    for (const path of paths) {
      try {
        const name = `${mode}-${path.replace(/\/$/, '').replaceAll('/', '-')}`;
        const samples = [];
        for (let run = 1; run <= runs; run++) {
          const chrome = await launch({ chromePath: chromium.executablePath(), chromeFlags, logLevel: 'error' });
          try {
            const result = await lighthouse(new URL(path, base).href, {
              port: chrome.port, logLevel: 'error', output: ['json', 'html'],
              onlyCategories: Object.keys(thresholds),
            }, mode === 'desktop' ? desktopConfig : undefined);
            if (!result || result.lhr.runtimeError) throw new Error(JSON.stringify(result?.lhr.runtimeError));
            if (result.lhr.configSettings.formFactor !== mode) throw new Error(`Incorrect Lighthouse form factor: ${result.lhr.configSettings.formFactor}`);
            await Promise.all(result.report.map((report, i) => writeFile(new URL(`${name}-run-${run}.${i ? 'html' : 'json'}`, output), report)));
            const scores = Object.fromEntries(Object.entries(result.lhr.categories).map(([key, value]) => [key, value.score]));
            samples.push({ run, scores, reports: result.report });
          } finally { await chrome.kill(); }
        }
        // Performance varies with host load. Use the median of independent,
        // cold-cache runs; deterministic quality checks must pass every run.
        const median = [...samples].sort((a, b) => a.scores.performance - b.scores.performance)[Math.floor(runs / 2)];
        await Promise.all(median.reports.map((report, i) => writeFile(new URL(`${name}.${i ? 'html' : 'json'}`, output), report)));
        const scores = Object.fromEntries(Object.keys(thresholds).map(key => [key,
          key === 'performance' ? median.scores[key] : Math.min(...samples.map(sample => sample.scores[key])),
        ]));
        const failures = Object.entries(thresholds).filter(([key, min]) => scores[key] < min).map(([key]) => key);
        if (failures.length) failed = true;
        const summary = { path, mode, scores, failures, representativeRun: median.run,
          samples: samples.map(({ run, scores }) => ({ run, scores })) };
        results.push(summary);
        console.log(JSON.stringify(summary));
      } catch (error) {
        failed = true;
        const summary = { path, mode, error: String(error) };
        results.push(summary);
        console.error(JSON.stringify(summary));
      }
    }
  }
} finally {
  await writeFile(new URL('summary.json', output), JSON.stringify(results, null, 2) + '\n');
  await server?.stop();
}
if (failed) process.exitCode = 1;

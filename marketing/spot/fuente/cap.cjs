// Captura scene.html cuadro por cuadro. Uso: node cap.cjs stills 1,5,9  |  node cap.cjs video out.mp4
const chromium = require('/home/claude/video/tools/node_modules/@sparticuz/chromium');
const puppeteer = require('/home/claude/video/tools/node_modules/puppeteer-core');
const { spawn } = require('child_process');
(async () => {
  const browser = await puppeteer.launch({ args: [...chromium.args, '--allow-file-access-from-files'], executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file://' + __dirname + '/scene.html', { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  const mode = process.argv[2];
  if (mode === 'stills') {
    for (const s of process.argv[3].split(',')) { await page.evaluate(t => render(t), +s); await page.screenshot({ path: `still_${s}.jpg`, type: 'jpeg', quality: 85 }); }
  } else {
    const fps = 30, total = await page.evaluate(() => TOTAL), n = Math.round(total * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-crf', '17', '-movflags', '+faststart', process.argv[3]], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => render(t), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log('frame', i, '/', n);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();

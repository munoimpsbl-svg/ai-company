const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const input = document.getElementById('imageInput');
const emptyState = document.getElementById('emptyState');
const statusEl = document.getElementById('status');
const depthRange = document.getElementById('depthRange');
const resetButton = document.getElementById('resetButton');
const demoButton = document.getElementById('demoButton');
const styleSelect = document.getElementById('styleSelect');

let image = null;
let sourceCanvas = null;
let styledCanvas = null;
let bricks = [];
let particles = [];
let paddle = { x: 0, y: 0, w: 120, h: 12 };
let ball = { x: 0, y: 0, r: 8, vx: 4, vy: -5 };
let running = false;
let gameOver = false;
let score = 0;
let lastTime = 0;

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  paddle.y = rect.height - 36;
  paddle.w = Math.max(92, rect.width * .14);
  if (!ball.x) resetBall();
  if (image) buildBricks();
}

function resetBall() {
  const w = canvas.clientWidth;
  ball = { x: w / 2, y: canvas.clientHeight - 66, r: 8, vx: 4, vy: -5 };
  paddle.x = w / 2 - paddle.w / 2;
}

function loadImage(img) {
  image = img;
  sourceCanvas = document.createElement('canvas');
  const sw = Math.max(1, img.naturalWidth || img.width);
  const sh = Math.max(1, img.naturalHeight || img.height);
  const scale = Math.min(1, 900 / Math.max(sw, sh));
  sourceCanvas.width = Math.round(sw * scale);
  sourceCanvas.height = Math.round(sh * scale);
  sourceCanvas.getContext('2d').drawImage(img, 0, 0, sourceCanvas.width, sourceCanvas.height);
  applyStyle();
  emptyState.classList.add('hidden');
  statusEl.textContent = '準備完了 — タップまたはクリックで開始';
  score = 0;
  buildBricks();
  resetBall();
  running = false;
  gameOver = false;
}

function colorDistance(a, b) {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]);
}

function nearestPaletteColor(r, g, b) {
  // ファミコン風の見た目用。厳密な実機再現ではなく、視認性を優先した限定色。
  const palette = [[0, 0, 0], [36, 36, 54], [76, 45, 50], [116, 54, 48], [170, 72, 54], [222, 115, 66], [244, 180, 83], [255, 226, 120], [43, 82, 69], [56, 133, 92], [100, 183, 103], [171, 219, 116], [42, 62, 112], [55, 104, 169], [95, 158, 201], [215, 235, 226]];
  return palette.reduce((best, color) => colorDistance([r, g, b], color) < colorDistance([r, g, b], best) ? color : best, palette[0]);
}

function applyFamicomStyle() {
  const w = Math.max(64, Math.round(sourceCanvas.width / 5));
  const h = Math.max(48, Math.round(sourceCanvas.height / 5));
  const low = document.createElement('canvas');
  low.width = w; low.height = h;
  const lowCtx = low.getContext('2d');
  lowCtx.imageSmoothingEnabled = false;
  lowCtx.drawImage(sourceCanvas, 0, 0, w, h);
  const data = lowCtx.getImageData(0, 0, w, h);
  for (let i = 0; i < data.data.length; i += 4) {
    const c = nearestPaletteColor(data.data[i], data.data[i + 1], data.data[i + 2]);
    data.data[i] = c[0]; data.data[i + 1] = c[1]; data.data[i + 2] = c[2];
  }
  lowCtx.putImageData(data, 0, 0);
  styledCanvas = document.createElement('canvas');
  styledCanvas.width = sourceCanvas.width; styledCanvas.height = sourceCanvas.height;
  const out = styledCanvas.getContext('2d');
  out.imageSmoothingEnabled = false;
  out.drawImage(low, 0, 0, styledCanvas.width, styledCanvas.height);
}

function applyPolygonStyle() {
  styledCanvas = document.createElement('canvas');
  styledCanvas.width = sourceCanvas.width; styledCanvas.height = sourceCanvas.height;
  const out = styledCanvas.getContext('2d');
  const cell = Math.max(32, Math.round(Math.min(sourceCanvas.width, sourceCanvas.height) / 8));
  out.fillStyle = '#111'; out.fillRect(0, 0, styledCanvas.width, styledCanvas.height);
  for (let y = 0; y < sourceCanvas.height; y += cell) for (let x = 0; x < sourceCanvas.width; x += cell) {
    const w = Math.min(cell, sourceCanvas.width - x), h = Math.min(cell, sourceCanvas.height - y);
    const sample = sourceCanvas.getContext('2d').getImageData(Math.min(x + w / 2, sourceCanvas.width - 1), Math.min(y + h / 2, sourceCanvas.height - 1), 1, 1).data;
    const shade = (Math.random() - .5) * 34;
    const rgb = [sample[0] + shade, sample[1] + shade, sample[2] + shade].map(v => Math.max(0, Math.min(255, v)));
    const split = Math.random() > .5;
    out.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
    out.beginPath();
    if (split) { out.moveTo(x, y); out.lineTo(x + w, y); out.lineTo(x, y + h); }
    else { out.moveTo(x + w, y); out.lineTo(x + w, y + h); out.lineTo(x, y + h); }
    out.closePath(); out.fill();
    out.fillStyle = `rgba(255,255,255,${Math.random() * .1})`;
    out.beginPath();
    if (split) { out.moveTo(x + w, y); out.lineTo(x + w, y + h); out.lineTo(x, y + h); }
    else { out.moveTo(x, y); out.lineTo(x + w, y); out.lineTo(x, y + h); }
    out.closePath(); out.fill();
  }
}

function applyStyle() {
  if (!sourceCanvas) return;
  if (styleSelect.value === 'famicom') applyFamicomStyle();
  else if (styleSelect.value === 'polygon') applyPolygonStyle();
  else styledCanvas = sourceCanvas;
}

function buildBricks() {
  const cols = canvas.clientWidth < 600 ? 8 : 12;
  const rows = 7;
  const gap = 4;
  const margin = 22;
  const width = (canvas.clientWidth - margin * 2 - gap * (cols - 1)) / cols;
  const height = Math.min(48, (canvas.clientHeight * .42 - gap * (rows - 1)) / rows);
  bricks = [];
  for (let row = 0; row < rows; row++) for (let col = 0; col < cols; col++) {
    const depth = Math.random() * Number(depthRange.value);
    const form = Math.random();
    bricks.push({
      x: margin + col * (width + gap), y: 26 + row * (height + gap), w: width, h: height,
      row, col, alive: true, depth,
      // 平面・レリーフ・立体を同じ画像内に混ぜる。
      geometry: form < .34 ? 'flat' : form < .68 ? 'relief' : 'solid',
      tilt: (Math.random() - .5) * (form < .34 ? .018 : .055)
    });
  }
}

function drawBrick(b) {
  if (!b.alive) return;
  const renderSource = styledCanvas || sourceCanvas;
  const sw = renderSource.width / 12, sh = renderSource.height / 7;
  const sx = b.col * sw, sy = b.row * sh;
  ctx.save();
  ctx.translate(b.x + b.w / 2, b.y + b.h / 2);
  ctx.rotate(b.tilt);
  const extrusion = b.geometry === 'flat' ? 0 : b.geometry === 'relief' ? Math.max(2, b.depth * .45) : Math.max(4, b.depth);
  // 立体ブロックは画像面の下に側面を先に描く。
  if (extrusion > 0) {
    ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 7;
    ctx.shadowOffsetX = extrusion * .55; ctx.shadowOffsetY = extrusion;
    ctx.fillStyle = b.geometry === 'solid' ? 'rgba(18,20,27,.92)' : 'rgba(36,39,47,.82)';
    ctx.fillRect(-b.w / 2 + extrusion * .35, -b.h / 2 + extrusion * .65, b.w, b.h);
    ctx.shadowColor = 'transparent';
  }
  ctx.shadowColor = b.geometry === 'flat' ? 'transparent' : 'rgba(0,0,0,.42)';
  ctx.shadowBlur = b.geometry === 'flat' ? 0 : 5;
  ctx.shadowOffsetX = extrusion * .35; ctx.shadowOffsetY = extrusion * .55;
  ctx.drawImage(renderSource, sx, sy, sw, sh, -b.w / 2, -b.h / 2, b.w, b.h);
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = b.geometry === 'flat' ? 'rgba(255,255,255,.025)' : `rgba(255,255,255,${.05 + extrusion / 240})`;
  ctx.fillRect(-b.w / 2, -b.h / 2, b.w, b.h);
  if (b.geometry !== 'flat') {
    ctx.strokeStyle = b.geometry === 'solid' ? 'rgba(255,255,255,.24)' : 'rgba(255,255,255,.12)';
    ctx.lineWidth = b.geometry === 'solid' ? 1.5 : 1;
    ctx.strokeRect(-b.w / 2, -b.h / 2, b.w, b.h);
  }
  ctx.restore();
}

function draw() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#0c0c10'; ctx.fillRect(0, 0, w, h);
  bricks.forEach(drawBrick);
  ctx.fillStyle = '#c7ff4d'; ctx.fillRect(paddle.x, paddle.y, paddle.w, paddle.h);
  ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
  particles = particles.filter(p => p.life > 0);
  particles.forEach(p => { p.x += p.vx; p.y += p.vy; p.life -= .035; ctx.fillStyle = `rgba(199,255,77,${p.life})`; ctx.fillRect(p.x, p.y, 3, 3); });
  ctx.fillStyle = 'rgba(255,255,255,.75)'; ctx.font = '12px system-ui'; ctx.fillText(`SCORE ${score}`, 22, h - 14);
}

function explode(b) { for (let i = 0; i < 8; i++) particles.push({ x: b.x + b.w / 2, y: b.y + b.h / 2, vx: (Math.random() - .5) * 5, vy: (Math.random() - .5) * 5, life: 1 }); }
function update(dt) {
  if (!running) return;
  ball.x += ball.vx * dt; ball.y += ball.vy * dt;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (ball.x < ball.r || ball.x > w - ball.r) ball.vx *= -1;
  if (ball.y < ball.r) ball.vy *= -1;
  if (ball.y > h + ball.r) {
    running = false;
    gameOver = true;
    statusEl.textContent = `ゲームオーバー — SCORE ${score}。リセットで再挑戦`;
    resetBall();
    return;
  }
  if (ball.y + ball.r > paddle.y && ball.y - ball.r < paddle.y + paddle.h && ball.x > paddle.x && ball.x < paddle.x + paddle.w) { ball.vy = -Math.abs(ball.vy); ball.vx += (ball.x - (paddle.x + paddle.w / 2)) * .035; }
  for (const b of bricks) if (b.alive && ball.x > b.x && ball.x < b.x + b.w && ball.y > b.y && ball.y < b.y + b.h) { b.alive = false; ball.vy *= -1; score += 10; explode(b); break; }
  if (bricks.length && bricks.every(b => !b.alive)) {
    running = false;
    gameOver = true;
    statusEl.textContent = `全破壊！ SCORE ${score} — リセットで再挑戦`;
  }
}
function loop(t) { const dt = Math.min((t - lastTime) / 16.67, 2); lastTime = t; update(dt); draw(); requestAnimationFrame(loop); }

function movePaddle(clientX) { const rect = canvas.getBoundingClientRect(); paddle.x = Math.max(0, Math.min(canvas.clientWidth - paddle.w, clientX - rect.left - paddle.w / 2)); if (!running && image) ball.x = paddle.x + paddle.w / 2; }
canvas.addEventListener('pointermove', e => movePaddle(e.clientX));
canvas.addEventListener('pointerdown', e => {
  movePaddle(e.clientX);
  if (image && !gameOver) { running = true; statusEl.textContent = '破壊中'; }
});
input.addEventListener('change', e => { const file = e.target.files[0]; if (!file) return; const img = new Image(); img.onload = () => loadImage(img); img.src = URL.createObjectURL(file); });
demoButton.addEventListener('click', () => { const c = document.createElement('canvas'); c.width = 1200; c.height = 700; const x = c.getContext('2d'); const g = x.createLinearGradient(0, 0, 1200, 700); g.addColorStop(0, '#5227a8'); g.addColorStop(1, '#ff7b54'); x.fillStyle = g; x.fillRect(0, 0, c.width, c.height); x.fillStyle = 'rgba(255,255,255,.8)'; x.font = 'bold 130px system-ui'; x.fillText('BREAK', 130, 320); x.fillStyle = '#c7ff4d'; x.font = 'bold 100px system-ui'; x.fillText('FRAME', 480, 500); const img = new Image(); img.onload = () => loadImage(img); img.src = c.toDataURL(); });
resetButton.addEventListener('click', () => {
  if (image) { buildBricks(); resetBall(); score = 0; running = false; gameOver = false; statusEl.textContent = '準備完了 — タップまたはクリックで開始'; }
});
depthRange.addEventListener('input', () => { if (image) buildBricks(); });
styleSelect.addEventListener('change', () => {
  if (!image) return;
  applyStyle();
  buildBricks();
  resetBall();
  running = false;
  gameOver = false;
  statusEl.textContent = `${styleSelect.options[styleSelect.selectedIndex].text} — タップまたはクリックで開始`;
});
window.addEventListener('resize', resize);
resize(); requestAnimationFrame(loop);

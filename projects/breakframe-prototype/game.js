const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const input = document.getElementById('imageInput');
const emptyState = document.getElementById('emptyState');
const statusEl = document.getElementById('status');
const depthRange = document.getElementById('depthRange');
const resetButton = document.getElementById('resetButton');
const demoButton = document.getElementById('demoButton');
const styleSelect = document.getElementById('styleSelect');
const fitSelect = document.getElementById('fitSelect');

let image = null;
let sourceCanvas = null;
let styledCanvas = null;
let renderCanvas = null;
let debris = [];
let bricks = [];
let particles = [];
let paddle = { x: 0, y: 0, w: 120, h: 12 };
let ball = { x: 0, y: 0, r: 8, vx: 4, vy: -5 };
let running = false;
let gameOver = false;
let score = 0;
let lastTime = 0;
let animationFrameId = 0;

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  paddle.y = rect.height - 36;
  paddle.w = Math.max(92, rect.width * .14);
  if (!ball.x) resetBall();
  if (image) { buildBricks(); prepareRenderCanvas(); draw(); }
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
  prepareRenderCanvas();
  resetBall();
  running = false;
  gameOver = false;
  draw();
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

function prepareRenderCanvas() {
  if (!styledCanvas || !canvas.clientWidth) return;
  const cols = 12, rows = 7, gap = 4, margin = 22;
  const width = Math.max(1, (canvas.clientWidth - margin * 2 - gap * (cols - 1)) / cols);
  const height = Math.max(1, Math.min(48, (canvas.clientHeight * .42 - gap * (rows - 1)) / rows));
  const gridWidth = Math.max(1, width * cols + gap * (cols - 1));
  const gridHeight = Math.max(1, height * rows + gap * (rows - 1));
  renderCanvas = document.createElement('canvas');
  renderCanvas.width = 1200;
  renderCanvas.height = Math.max(1, Math.round(1200 * gridHeight / gridWidth));
  const out = renderCanvas.getContext('2d');
  const sw = styledCanvas.width, sh = styledCanvas.height;
  const scale = fitSelect.value === 'cover'
    ? Math.max(renderCanvas.width / sw, renderCanvas.height / sh)
    : Math.min(renderCanvas.width / sw, renderCanvas.height / sh);
  const dw = sw * scale, dh = sh * scale;
  out.fillStyle = '#0c0c10';
  out.fillRect(0, 0, renderCanvas.width, renderCanvas.height);
  out.imageSmoothingEnabled = fitSelect.value !== 'cover';
  out.drawImage(styledCanvas, (renderCanvas.width - dw) / 2, (renderCanvas.height - dh) / 2, dw, dh);
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

function cameraScaleAt(y) {
  const h = canvas.clientHeight;
  const t = Math.max(0, Math.min(1, y / (h * .92)));
  return .52 + t * .58;
}
function cameraProject(x, y) {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const t = Math.max(0, Math.min(1, y / (h * .92)));
  const scale = cameraScaleAt(y);
  return { x: w / 2 + (x - w / 2) * scale, y: h * .12 + t * h * .76, scale };
}
function cameraUnprojectX(screenX, worldY) {
  const w = canvas.clientWidth;
  const scale = cameraScaleAt(worldY);
  return w / 2 + (screenX - w / 2) / scale;
}
function drawMountainClimbSurface(w, h) {
  const horizon = h * .12, base = h * .94, center = w / 2;
  ctx.save();
  ctx.fillStyle = 'rgba(8,12,20,.42)';
  ctx.beginPath(); ctx.moveTo(center - 8, horizon); ctx.lineTo(w * .04, base); ctx.lineTo(w * .96, base); ctx.lineTo(center + 8, horizon); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(199,255,77,.22)'; ctx.lineWidth = 1.5;
  for (let i = 0; i <= 8; i++) {
    const t = i / 8, y = horizon + Math.pow(t, 1.7) * (base - horizon), half = 12 + t * w * .44;
    ctx.beginPath(); ctx.moveTo(center - half, y); ctx.lineTo(center + half, y); ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(199,255,77,.16)';
  for (const side of [-1, 1]) { ctx.beginPath(); ctx.moveTo(center + side * 8, horizon); ctx.lineTo(center + side * w * .46, base); ctx.stroke(); }
  ctx.restore();
}
function drawBrick(b) {
  if (!b.alive) return;
  const renderSource = renderCanvas || styledCanvas || sourceCanvas;
  const sw = renderSource.width / 12, sh = renderSource.height / 7;
  const sx = b.col * sw, sy = b.row * sh;
  const extrusion = b.geometry === 'flat' ? 0 : b.geometry === 'relief' ? Math.max(2, b.depth * .45) : Math.max(5, b.depth);
  const perspective = b.geometry === 'solid' ? Math.min(.16, extrusion / 160) : b.geometry === 'relief' ? Math.min(.07, extrusion / 260) : 0;
  const p = cameraProject(b.x + b.w / 2, b.y + b.h / 2);
  const bw = b.w * p.scale, bh = b.h * p.scale, ex = extrusion * .62 * p.scale, ey = extrusion * p.scale;
  const light = b.geometry === 'solid' ? 'rgba(255,255,255,.24)' : 'rgba(255,255,255,.12)';
  const shade = b.geometry === 'solid' ? 'rgba(12,15,22,.82)' : 'rgba(30,34,42,.68)';
  ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(b.tilt);
  if (extrusion > 0) {
    ctx.shadowColor = 'rgba(0,0,0,.58)'; ctx.shadowBlur = 8 * p.scale; ctx.shadowOffsetX = ex; ctx.shadowOffsetY = ey;
    ctx.fillStyle = shade;
    ctx.beginPath(); ctx.moveTo(bw / 2, -bh / 2); ctx.lineTo(bw / 2 + ex, -bh / 2 + ey); ctx.lineTo(bw / 2 + ex, bh / 2 + ey); ctx.lineTo(bw / 2, bh / 2); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(9,12,18,.72)';
    ctx.beginPath(); ctx.moveTo(-bw / 2, -bh / 2); ctx.lineTo(-bw / 2 - ex * .35, -bh / 2 + ey * .7); ctx.lineTo(-bw / 2 - ex * .35, bh / 2 + ey * .7); ctx.lineTo(-bw / 2, bh / 2); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(6,8,12,.9)';
    ctx.beginPath(); ctx.moveTo(-bw / 2, bh / 2); ctx.lineTo(bw / 2, bh / 2); ctx.lineTo(bw / 2 + ex, bh / 2 + ey); ctx.lineTo(-bw / 2 - ex * .35, bh / 2 + ey * .7); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = light; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-bw / 2, -bh / 2); ctx.lineTo(bw / 2, -bh / 2); ctx.stroke(); ctx.shadowColor = 'transparent';
  }
  ctx.save(); ctx.transform(1, 0, perspective, 1, 0, 0);
  ctx.shadowColor = b.geometry === 'flat' ? 'transparent' : 'rgba(0,0,0,.38)';
  ctx.shadowBlur = b.geometry === 'flat' ? 0 : 5 * p.scale;
  ctx.drawImage(renderSource, sx, sy, sw, sh, -bw / 2, -bh / 2, bw, bh);
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = b.geometry === 'flat' ? 'rgba(255,255,255,.025)' : light; ctx.fillRect(-bw / 2, -bh / 2, bw, bh);
  if (b.geometry !== 'flat') { ctx.strokeStyle = light; ctx.lineWidth = b.geometry === 'solid' ? 1.5 : 1; ctx.strokeRect(-bw / 2, -bh / 2, bw, bh); }
  ctx.restore(); ctx.restore();
}
function drawDebris(d) {
  const p = cameraProject(d.x, d.y), s = Math.max(2, d.size * p.scale * Math.abs(Math.cos(d.spin)));
  ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(d.angle); ctx.fillStyle = d.color;
  ctx.beginPath(); ctx.moveTo(-s, -d.size * p.scale / 2); ctx.lineTo(s, -d.size * p.scale / 2); ctx.lineTo(s + d.depth * p.scale, d.size * p.scale / 2 + d.depth * p.scale); ctx.lineTo(-s + d.depth * p.scale, d.size * p.scale / 2 + d.depth * p.scale); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.fillRect(-s, -d.size * p.scale / 2, s * 2, Math.max(1, d.size * p.scale * .12)); ctx.restore();
}
function drawMountainEnvironment(w, h) {
  const sky = ctx.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0, '#111b35'); sky.addColorStop(.48, '#27324a'); sky.addColorStop(1, '#090b12');
  ctx.fillStyle = sky; ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = 'rgba(122,150,190,.22)';
  ctx.beginPath(); ctx.moveTo(0, h * .42); ctx.lineTo(w * .18, h * .22); ctx.lineTo(w * .34, h * .39); ctx.lineTo(w * .53, h * .16); ctx.lineTo(w * .7, h * .36); ctx.lineTo(w * .88, h * .2); ctx.lineTo(w, h * .4); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(9,12,20,.7)';
  ctx.beginPath(); ctx.moveTo(0, h * .58); ctx.lineTo(w * .23, h * .42); ctx.lineTo(w * .43, h * .56); ctx.lineTo(w * .66, h * .35); ctx.lineTo(w, h * .55); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fill();
  const horizon = h * .43;
  ctx.strokeStyle = 'rgba(199,255,77,.12)'; ctx.lineWidth = 1;
  for (let i = -8; i <= 8; i++) { ctx.beginPath(); ctx.moveTo(w / 2, horizon); ctx.lineTo(w / 2 + i * w * .16, h); ctx.stroke(); }
  for (let i = 0; i < 6; i++) { const y = horizon + Math.pow((i + 1) / 6, 1.7) * (h - horizon); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
}
function draw() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  drawMountainEnvironment(w, h);
  drawMountainClimbSurface(w, h);
  bricks.forEach(drawBrick);
  debris = debris.filter(d => d.life > 0);
  debris.forEach(d => { d.x += d.vx; d.y += d.vy; d.vy += .08; d.angle += d.spin; d.spin *= .995; d.life -= .035; drawDebris(d); });
  const paddleProjection = cameraProject(paddle.x + paddle.w / 2, paddle.y + paddle.h / 2);
  ctx.save(); ctx.translate(paddleProjection.x, paddleProjection.y); ctx.scale(paddleProjection.scale, paddleProjection.scale);
  ctx.fillStyle = '#c7ff4d'; ctx.fillRect(-paddle.w / 2, -paddle.h / 2, paddle.w, paddle.h); ctx.restore();
  const ballProjection = cameraProject(ball.x, ball.y);
  ctx.beginPath(); ctx.arc(ballProjection.x, ballProjection.y, ball.r * ballProjection.scale, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
  particles = particles.filter(p => p.life > 0);
  particles.forEach(p => { p.x += p.vx; p.y += p.vy; p.life -= .035; const pp = cameraProject(p.x, p.y); ctx.fillStyle = 'rgba(199,255,77,' + p.life + ')'; ctx.fillRect(pp.x, pp.y, 3 * pp.scale, 3 * pp.scale); });
  ctx.fillStyle = 'rgba(255,255,255,.75)'; ctx.font = '12px system-ui'; ctx.fillText(`SCORE ${score}`, 22, h - 14);
}

function explode(b) {
  for (let i = 0; i < 8; i++) {
    const color = b.geometry === 'solid' ? 'rgba(199,255,77,.82)' : 'rgba(255,255,255,.7)';
    debris.push({ x: b.x + b.w / 2, y: b.y + b.h / 2, vx: (Math.random() - .5) * 5, vy: (Math.random() - .5) * 5 - 1, life: 1, angle: Math.random() * Math.PI, spin: (Math.random() - .5) * .28, size: 4 + Math.random() * 8, depth: b.depth * .25, color });
    particles.push({ x: b.x + b.w / 2, y: b.y + b.h / 2, vx: (Math.random() - .5) * 5, vy: (Math.random() - .5) * 5, life: 1 });
  }
}
function update(dt) {
  if (!running) return;
  ball.x += ball.vx * dt; ball.y += ball.vy * dt;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (ball.x < ball.r || ball.x > w - ball.r) ball.vx *= -1;
  if (ball.y < ball.r) ball.vy *= -1;
  if (ball.y > h + ball.r) {
    running = false;
    gameOver = true;
    statusEl.textContent = `ゲームオーバー — SCORE ${score}。再開するか選択してください`;
    resetBall();
    window.setTimeout(() => {
      if (!image || !gameOver) return;
      const retry = window.confirm('ゲームオーバーです。最初から再開しますか？');
      if (retry) {
        buildBricks(); resetBall(); score = 0; debris = []; particles = [];
        gameOver = false; running = true; statusEl.textContent = '再開しました — 破壊中'; startLoop();
      } else statusEl.textContent = `ゲームオーバー — SCORE ${score}。リセットで再挑戦`;
    }, 80);
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
function startLoop() {
  if (!animationFrameId) { lastTime = performance.now(); animationFrameId = requestAnimationFrame(loop); }
}
function loop(t) {
  const dt = Math.min((t - lastTime) / 16.67, 2); lastTime = t;
  update(dt); draw();
  if (running || debris.length || particles.length) animationFrameId = requestAnimationFrame(loop);
  else animationFrameId = 0;
}

function movePaddle(clientX) {
  const rect = canvas.getBoundingClientRect();
  const screenX = clientX - rect.left;
  // 入力は画面座標なので、パドルのワールドYにおける投影倍率を戻してから物理座標へ入れる。
  const worldX = cameraUnprojectX(screenX, paddle.y + paddle.h / 2);
  paddle.x = Math.max(0, Math.min(canvas.clientWidth - paddle.w, worldX - paddle.w / 2));
  if (!running && image) ball.x = paddle.x + paddle.w / 2;
}
canvas.addEventListener('pointermove', e => {
  if (e.isPrimary !== false) movePaddle(e.clientX);
});
canvas.addEventListener('pointerdown', e => {
  if (e.isPrimary !== false) {
    e.preventDefault();
    canvas.setPointerCapture?.(e.pointerId);
    movePaddle(e.clientX);
    if (image && !gameOver) { running = true; statusEl.textContent = '破壊中'; startLoop(); }
  }
});
canvas.addEventListener('pointerup', e => {
  if (canvas.hasPointerCapture?.(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
});
canvas.addEventListener('pointercancel', e => {
  if (canvas.hasPointerCapture?.(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
});
input.addEventListener('change', e => { const file = e.target.files[0]; if (!file) return; const img = new Image(); img.onload = () => loadImage(img); img.src = URL.createObjectURL(file); });
demoButton.addEventListener('click', () => { const c = document.createElement('canvas'); c.width = 1200; c.height = 700; const x = c.getContext('2d'); const g = x.createLinearGradient(0, 0, 1200, 700); g.addColorStop(0, '#5227a8'); g.addColorStop(1, '#ff7b54'); x.fillStyle = g; x.fillRect(0, 0, c.width, c.height); x.fillStyle = 'rgba(255,255,255,.8)'; x.font = 'bold 130px system-ui'; x.fillText('BREAK', 130, 320); x.fillStyle = '#c7ff4d'; x.font = 'bold 100px system-ui'; x.fillText('FRAME', 480, 500); const img = new Image(); img.onload = () => loadImage(img); img.src = c.toDataURL(); });
resetButton.addEventListener('click', () => {
  if (image) { buildBricks(); resetBall(); score = 0; running = false; gameOver = false; debris = []; particles = []; statusEl.textContent = '準備完了 — タップまたはクリックで開始'; draw(); }
});
depthRange.addEventListener('input', () => { if (image) { buildBricks(); prepareRenderCanvas(); } });
fitSelect.addEventListener('change', () => { if (image) { buildBricks(); prepareRenderCanvas(); resetBall(); running = false; statusEl.textContent = `${fitSelect.options[fitSelect.selectedIndex].text} — タップまたはクリックで開始`; } });
styleSelect.addEventListener('change', () => {
  if (!image) return;
  applyStyle();
  buildBricks();
  prepareRenderCanvas();
  resetBall();
  running = false;
  gameOver = false;
  statusEl.textContent = `${styleSelect.options[styleSelect.selectedIndex].text} — タップまたはクリックで開始`;
});
window.addEventListener('resize', resize);
resize(); draw();

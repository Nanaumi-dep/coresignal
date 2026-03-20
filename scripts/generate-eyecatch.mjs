import sharp from "sharp";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { mkdirSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputPath = resolve(__dirname, "../public/images/default-eyecatch.png");

mkdirSync(dirname(outputPath), { recursive: true });

const width = 1200;
const height = 630;

// シグナル波形のパスを生成
function generateSignalPath() {
  const points = [];
  const startX = 750;
  const endX = 1150;
  const centerY = 180;
  const segments = 40;

  for (let i = 0; i <= segments; i++) {
    const x = startX + (endX - startX) * (i / segments);
    const progress = i / segments;
    // 減衰する波形
    const amplitude = 40 * Math.exp(-progress * 2.5);
    const y = centerY + amplitude * Math.sin(progress * Math.PI * 8);
    points.push(`${x},${y}`);
  }

  return `M${points.join(" L")}`;
}

const signalPath = generateSignalPath();

const svg = `
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- 背景グラデーション -->
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a1628"/>
      <stop offset="100%" style="stop-color:#0d1f3c"/>
    </linearGradient>

    <!-- アクセントグロー -->
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="glow-strong">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- 背景 -->
  <rect width="${width}" height="${height}" fill="url(#bg)"/>

  <!-- グリッドパターン（薄い） -->
  <g opacity="0.04" stroke="#00D4FF">
    ${Array.from({ length: 13 }, (_, i) => `<line x1="${i * 100}" y1="0" x2="${i * 100}" y2="${height}" stroke-width="1"/>`).join("")}
    ${Array.from({ length: 7 }, (_, i) => `<line x1="0" y1="${i * 100}" x2="${width}" y2="${i * 100}" stroke-width="1"/>`).join("")}
  </g>

  <!-- シグナル波形（右上） -->
  <path d="${signalPath}" fill="none" stroke="#00D4FF" stroke-width="2.5" opacity="0.6" filter="url(#glow)"/>

  <!-- ドットアクセント -->
  <circle cx="1150" cy="180" r="4" fill="#00D4FF" opacity="0.8" filter="url(#glow)"/>
  <circle cx="750" cy="180" r="3" fill="#00D4FF" opacity="0.4"/>

  <!-- サイト名 -->
  <text x="600" y="320" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="72" font-weight="900" letter-spacing="-2">
    <tspan fill="#e94560">Core</tspan><tspan fill="#ffffff">Signal</tspan>
  </text>

  <!-- サブテキスト -->
  <text x="600" y="380" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Kaku Gothic ProN', sans-serif" font-size="22" fill="#00D4FF" opacity="0.9" letter-spacing="2">
    ガジェット × クレジットカード × デスクセットアップ
  </text>

  <!-- 下部のライン -->
  <line x1="400" y1="430" x2="800" y2="430" stroke="#00D4FF" stroke-width="1" opacity="0.2"/>

  <!-- 左下の装飾ドット -->
  <circle cx="80" cy="550" r="2" fill="#00D4FF" opacity="0.2"/>
  <circle cx="100" cy="560" r="1.5" fill="#00D4FF" opacity="0.15"/>
  <circle cx="60" cy="570" r="1" fill="#e94560" opacity="0.2"/>
</svg>
`;

await sharp(Buffer.from(svg))
  .png()
  .toFile(outputPath);

const { size } = await sharp(outputPath).metadata();
const stats = await import("fs").then((fs) => fs.statSync(outputPath));
console.log(`Generated: ${outputPath}`);
console.log(`Size: ${(stats.size / 1024).toFixed(1)} KB`);
console.log(`Dimensions: ${width}x${height}`);

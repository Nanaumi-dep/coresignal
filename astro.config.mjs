import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

// セキュリティメモ:
// - HTTPSリダイレクトはCloudFrontで設定済み（Astro側での実装不要）
// - セキュリティヘッダーはCloudFront Functions（coresignal-security-headers）で設定済み:
//   - Strict-Transport-Security: max-age=31536000; includeSubDomains
//   - X-Frame-Options: DENY
//   - X-Content-Type-Options: nosniff
//   - Referrer-Policy: strict-origin-when-cross-origin

export default defineConfig({
  site: "https://coresignal.jp",
  integrations: [mdx(), sitemap()],
  vite: { plugins: [tailwindcss()] },
});

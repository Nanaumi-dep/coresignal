import { getCollection } from "astro:content";

// XML特殊文字のエスケープ
function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

// "2026-07-25T20:00" / "2026-07-25" → RFC 822 形式（JSTとして解釈）
function toRfc822(dateStr) {
  const iso = dateStr.length <= 10 ? `${dateStr}T00:00:00+09:00` : `${dateStr}:00+09:00`;
  const d = new Date(iso);
  return d.toUTCString();
}

export async function GET(context) {
  const site = context.site?.toString().replace(/\/$/, "") ?? "https://coresignal.jp";

  const posts = (await getCollection("posts")).sort(
    (a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime()
  );

  const items = posts
    .slice(0, 30)
    .map((post) => {
      const slug = post.id.replace(/\.mdx$/, "").split("/").pop();
      const url = `${site}/${post.data.category}/${slug}/`;
      return `    <item>
      <title>${esc(post.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <description>${esc(post.data.description)}</description>
      <pubDate>${toRfc822(post.data.date)}</pubDate>
      <category>${esc(post.data.category)}</category>
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CoreSignal</title>
    <link>${site}/</link>
    <atom:link href="${site}/rss.xml" rel="self" type="application/rss+xml" />
    <description>エンジニア目線で、選ぶ基準を整理する。ガジェットとクレジットカードのメディア CoreSignal の新着記事</description>
    <language>ja</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}

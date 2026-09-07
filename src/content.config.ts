import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const posts = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/posts" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.string(),
    dateModified: z.string().optional(),
    category: z.string(),
    tags: z.array(z.string()).default([]),
    eyecatch: z.string().default("/images/site/about-banner.png"),
    // eyecatch にメーカー公式素材等の第三者提供画像を使う場合の出所明示（著作権法48条対応）。
    // 自作グラフィック（選び方ガイド・クレカ記事）では未指定にする。
    imageSource: z.string().optional(),
    imageSourceUrl: z.string().optional(),
    imageSourceDate: z.string().optional(),
    affiliate: z.boolean().default(false),
    brand: z.string().optional(),
    productName: z.string().optional(),
    compatibleWith: z.array(z.string()).default([]),
  }),
});

export const collections = { posts };

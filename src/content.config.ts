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
    affiliate: z.boolean().default(false),
    brand: z.string().optional(),
    productName: z.string().optional(),
    compatibleWith: z.array(z.string()).default([]),
  }),
});

export const collections = { posts };

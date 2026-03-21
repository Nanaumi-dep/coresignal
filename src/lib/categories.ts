export const CATEGORIES = [
  { name: "ガジェット", slug: "gadget", color: "#7B2FBE" },
  { name: "クレジットカード", slug: "creditcard", color: "#2196F3" },
] as const;

export type CategorySlug = (typeof CATEGORIES)[number]["slug"];

export const CATEGORY_MAP = Object.fromEntries(
  CATEGORIES.map((c) => [c.slug, c])
) as Record<CategorySlug, (typeof CATEGORIES)[number]>;

export function isValidCategory(slug: string): slug is CategorySlug {
  return CATEGORIES.some((c) => c.slug === slug);
}

export function getPostUrl(post: { id: string; data: { category: string } }): string {
  const slug = post.id.includes("/") ? post.id.split("/").pop()! : post.id;
  return `/${post.data.category}/${slug}/`;
}

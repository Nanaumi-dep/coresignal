export const CATEGORIES = [
  { name: "ガジェット", slug: "gadget", color: "#e94560" },
  { name: "クレジットカード", slug: "creditcard", color: "#2196F3" },
  { name: "デスクセットアップ", slug: "desk-setup", color: "#4ECDC4" },
  { name: "開発環境", slug: "dev-env", color: "#7B2FBE" },
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

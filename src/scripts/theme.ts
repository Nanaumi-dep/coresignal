/**
 * テーマ切替ロジック
 * - localStorage からテーマを復元
 * - OS設定（prefers-color-scheme）に追従
 * - トグルボタンで手動切替
 * - セキュリティ: localStorage の値は "light" / "dark" のみ許可
 */

const STORAGE_KEY = "theme";
const VALID_THEMES = ["light", "dark"] as const;
type Theme = (typeof VALID_THEMES)[number];

function sanitizeTheme(value: unknown): Theme | null {
  if (typeof value === "string" && VALID_THEMES.includes(value as Theme)) {
    return value as Theme;
  }
  return null;
}

function getStoredTheme(): Theme | null {
  try {
    return sanitizeTheme(localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

function getSystemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function getCurrentTheme(): Theme {
  return getStoredTheme() ?? getSystemTheme();
}

function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
  updateToggleIcons(theme);
}

function updateToggleIcons(theme: Theme): void {
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    const sunIcon = btn.querySelector("[data-icon-sun]");
    const moonIcon = btn.querySelector("[data-icon-moon]");
    if (sunIcon && moonIcon) {
      sunIcon.classList.toggle("hidden", theme !== "dark");
      moonIcon.classList.toggle("hidden", theme === "dark");
    }
  });
}

export function initTheme(): void {
  applyTheme(getCurrentTheme());

  // OS設定の変更を監視
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      if (!getStoredTheme()) {
        applyTheme(getSystemTheme());
      }
    });

  // トグルボタンのイベント
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next: Theme = getCurrentTheme() === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // localStorage が使えない環境でも動作する
      }
      applyTheme(next);
    });
  });
}

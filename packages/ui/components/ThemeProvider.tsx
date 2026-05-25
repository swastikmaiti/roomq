"use client";

/**
 * Minimal light/dark theme. Persists the choice to localStorage and toggles the
 * `dark` class on <html> (Tailwind `darkMode: "class"`). A tiny inline script in
 * the root layout applies the stored theme before paint to avoid a flash.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";

const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({
  theme: "light",
  toggle: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const stored = (localStorage.getItem("theme") as Theme | null) ?? "light";
    setTheme(stored);
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      return next;
    });
  }, []);

  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);

/** Script string injected before paint so the stored theme has no flash. */
export const themeInitScript = `
try {
  if (localStorage.theme === 'dark') document.documentElement.classList.add('dark');
} catch (_) {}
`;

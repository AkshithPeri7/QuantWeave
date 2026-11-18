"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { api, UserPreferences } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export type ThemeId = "signal-loom" | "daybreak" | "nebula" | "oceanic";
export type AvatarPresetId =
  | "loom"
  | "aqua"
  | "amber"
  | "violet"
  | "emerald"
  | "slate";
export type ColorMode = "system" | "dark" | "light";

export interface ThemeDefinition {
  id: ThemeId;
  name: string;
  category: "dark" | "light";
  tagline: string;
  background: string;
  surface: string;
  elevated: string;
  border: string;
  primaryAccent: string;
  secondaryAccent: string;
  primaryText: string;
  secondaryText: string;
}

export const THEMES: ThemeDefinition[] = [
  {
    id: "signal-loom",
    name: "Signal Loom",
    category: "dark",
    tagline: "Institutional Deep Dark with Luminous Periwinkle & Signal Aqua",
    background: "#080D19",
    surface: "#101A2B",
    elevated: "#142035",
    border: "#26344A",
    primaryAccent: "#8E91FF",
    secondaryAccent: "#54DCC5",
    primaryText: "#F2F4FF",
    secondaryText: "#A6B6CC",
  },
  {
    id: "daybreak",
    name: "Daybreak",
    category: "light",
    tagline: "Crisp High-Contrast Professional Daylight Surface",
    background: "#F5F7FC",
    surface: "#FFFFFF",
    elevated: "#EBF0F8",
    border: "#D4DEEB",
    primaryAccent: "#5E65DF",
    secondaryAccent: "#148E85",
    primaryText: "#17243C",
    secondaryText: "#52627A",
  },
  {
    id: "nebula",
    name: "Nebula",
    category: "dark",
    tagline: "Cosmic Ultraviolet & Galactic Violet Analytical Palette",
    background: "#120D23",
    surface: "#1C1530",
    elevated: "#241936",
    border: "#382956",
    primaryAccent: "#B798FF",
    secondaryAccent: "#F3A5CF",
    primaryText: "#F8F0FF",
    secondaryText: "#BCAECC",
  },
  {
    id: "oceanic",
    name: "Oceanic",
    category: "dark",
    tagline: "Deep Marine Cyan & Algorithmic Electric Teal",
    background: "#071A1D",
    surface: "#0C2328",
    elevated: "#102A30",
    border: "#1D3D44",
    primaryAccent: "#42D6C1",
    secondaryAccent: "#76B6E5",
    primaryText: "#EDFDFC",
    secondaryText: "#9EBFC3",
  },
];

interface ThemeContextType {
  theme: ThemeId;
  resolvedTheme: ThemeId;
  avatarPreset: AvatarPresetId;
  colorMode: ColorMode;
  reducedMotion: boolean;
  isLoadingPreferences: boolean;
  setTheme: (theme: ThemeId) => Promise<void>;
  setAvatarPreset: (preset: AvatarPresetId) => Promise<void>;
  setColorMode: (mode: ColorMode) => Promise<void>;
  setReducedMotion: (reduced: boolean) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  const [theme, setThemeState] = useState<ThemeId>("signal-loom");
  const [avatarPreset, setAvatarPresetState] = useState<AvatarPresetId>("loom");
  const [colorMode, setColorModeState] = useState<ColorMode>("system");
  const [reducedMotion, setReducedMotionState] = useState<boolean>(false);
  const [isLoadingPreferences, setIsLoadingPreferences] = useState<boolean>(true);
  const [systemIsLight, setSystemIsLight] = useState<boolean>(false);

  // Initialize from localStorage and system preference on client mount
  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem("qw_theme") as ThemeId | null;
      if (
        storedTheme &&
        ["signal-loom", "daybreak", "nebula", "oceanic"].includes(storedTheme)
      ) {
        setThemeState(storedTheme);
      }

      const storedAvatar = localStorage.getItem("qw_avatar_preset") as AvatarPresetId | null;
      if (
        storedAvatar &&
        ["loom", "aqua", "amber", "violet", "emerald", "slate"].includes(storedAvatar)
      ) {
        setAvatarPresetState(storedAvatar);
      }

      const storedMode = localStorage.getItem("qw_color_mode") as ColorMode | null;
      if (storedMode && ["system", "dark", "light"].includes(storedMode)) {
        setColorModeState(storedMode);
      }

      const storedMotion = localStorage.getItem("qw_reduced_motion");
      if (storedMotion !== null) {
        setReducedMotionState(storedMotion === "true");
      }

      // Check system color scheme
      const mediaQuery = window.matchMedia("(prefers-color-scheme: light)");
      setSystemIsLight(mediaQuery.matches);

      const handleSystemChange = (e: MediaQueryListEvent) => {
        setSystemIsLight(e.matches);
      };
      mediaQuery.addEventListener("change", handleSystemChange);

      return () => {
        mediaQuery.removeEventListener("change", handleSystemChange);
      };
    } catch {
      // localStorage may fail in restricted sandbox / privacy mode
    }
  }, []);

  // Compute resolved theme based on colorMode
  const resolvedTheme: ThemeId = useMemo(() => {
    if (colorMode === "light") {
      return theme === "daybreak" ? "daybreak" : "daybreak";
    }
    if (colorMode === "dark") {
      return theme === "daybreak" ? "signal-loom" : theme;
    }
    // system mode: if OS is light and user has not locked an explicit dark theme
    if (systemIsLight && theme === "daybreak") {
      return "daybreak";
    }
    return theme;
  }, [theme, colorMode, systemIsLight]);

  // Apply resolved theme attribute and motion class to root <html> element
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", resolvedTheme);

    if (reducedMotion) {
      root.classList.add("reduced-motion");
    } else {
      root.classList.remove("reduced-motion");
    }
  }, [resolvedTheme, reducedMotion]);

  // Synchronize authenticated user preferences from backend
  useEffect(() => {
    let isMounted = true;
    if (user) {
      api
        .getUserPreferences()
        .then((prefs: UserPreferences) => {
          if (!isMounted) return;
          if (
            prefs.theme &&
            ["signal-loom", "daybreak", "nebula", "oceanic"].includes(prefs.theme)
          ) {
            setThemeState(prefs.theme as ThemeId);
            localStorage.setItem("qw_theme", prefs.theme);
          }
          if (
            prefs.avatar_preset &&
            ["loom", "aqua", "amber", "violet", "emerald", "slate"].includes(
              prefs.avatar_preset
            )
          ) {
            setAvatarPresetState(prefs.avatar_preset as AvatarPresetId);
            localStorage.setItem("qw_avatar_preset", prefs.avatar_preset);
          }
          if (
            prefs.color_mode &&
            ["system", "dark", "light"].includes(prefs.color_mode)
          ) {
            setColorModeState(prefs.color_mode as ColorMode);
            localStorage.setItem("qw_color_mode", prefs.color_mode);
          }
          if (typeof prefs.reduced_motion === "boolean") {
            setReducedMotionState(prefs.reduced_motion);
            localStorage.setItem("qw_reduced_motion", String(prefs.reduced_motion));
          }
          setIsLoadingPreferences(false);
        })
        .catch(() => {
          if (isMounted) setIsLoadingPreferences(false);
        });
    } else {
      setIsLoadingPreferences(false);
    }

    return () => {
      isMounted = false;
    };
  }, [user]);

  // Handler for setting theme
  const setTheme = useCallback(
    async (newTheme: ThemeId) => {
      setThemeState(newTheme);
      try {
        localStorage.setItem("qw_theme", newTheme);
      } catch {}

      if (user) {
        try {
          await api.updateUserPreferences({ theme: newTheme });
        } catch {
          // silently continue on background network failure
        }
      }
    },
    [user]
  );

  // Handler for setting avatar preset
  const setAvatarPreset = useCallback(
    async (newPreset: AvatarPresetId) => {
      setAvatarPresetState(newPreset);
      try {
        localStorage.setItem("qw_avatar_preset", newPreset);
      } catch {}

      if (user) {
        try {
          await api.updateUserPreferences({ avatar_preset: newPreset });
        } catch {
          // silently continue
        }
      }
    },
    [user]
  );

  // Handler for setting color mode
  const setColorMode = useCallback(
    async (newMode: ColorMode) => {
      setColorModeState(newMode);
      try {
        localStorage.setItem("qw_color_mode", newMode);
      } catch {}

      // If user chooses light, set default theme to daybreak if not already
      if (newMode === "light" && theme !== "daybreak") {
        setThemeState("daybreak");
        try {
          localStorage.setItem("qw_theme", "daybreak");
        } catch {}
      } else if (newMode === "dark" && theme === "daybreak") {
        setThemeState("signal-loom");
        try {
          localStorage.setItem("qw_theme", "signal-loom");
        } catch {}
      }

      if (user) {
        try {
          await api.updateUserPreferences({
            color_mode: newMode,
            theme: newMode === "light" ? "daybreak" : theme === "daybreak" ? "signal-loom" : theme,
          });
        } catch {}
      }
    },
    [user, theme]
  );

  // Handler for setting reduced motion
  const setReducedMotion = useCallback(
    async (reduced: boolean) => {
      setReducedMotionState(reduced);
      try {
        localStorage.setItem("qw_reduced_motion", String(reduced));
      } catch {}

      if (user) {
        try {
          await api.updateUserPreferences({ reduced_motion: reduced });
        } catch {}
      }
    },
    [user]
  );

  return (
    <ThemeContext.Provider
      value={{
        theme,
        resolvedTheme,
        avatarPreset,
        colorMode,
        reducedMotion,
        isLoadingPreferences,
        setTheme,
        setAvatarPreset,
        setColorMode,
        setReducedMotion,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

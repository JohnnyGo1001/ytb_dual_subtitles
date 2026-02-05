import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Theme } from '@/types/common';

// Context类型定义
interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

// 创建Context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Provider组件
interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>('dark');

  useEffect(() => {
    // 从localStorage读取主题设置
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      setTheme(savedTheme);
    } else {
      // 默认使用暗色主题
      setTheme('dark');
    }
  }, []);

  useEffect(() => {
    // 更新HTML元素的data-theme属性
    document.documentElement.setAttribute('data-theme', theme);
    // 保存到localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// 自定义Hook
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
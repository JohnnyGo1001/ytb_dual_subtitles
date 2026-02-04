import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '@/contexts/ThemeContext';
import ConnectionStatus from '@/components/ConnectionStatus';
import styles from './index.module.css';

function Header() {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link to="/" className={styles.logo}>
          YouTube双语字幕
        </Link>

        <nav className={styles.nav}>
          <Link
            to="/"
            className={`${styles.navLink} ${location.pathname === '/' ? styles.active : ''}`}
          >
            视频列表
          </Link>
          <Link
            to="/downloads"
            className={`${styles.navLink} ${location.pathname === '/downloads' ? styles.active : ''}`}
          >
            下载
          </Link>
        </nav>

        <div className={styles.headerActions}>
          <ConnectionStatus className={styles.connectionStatus} />
          <button
            onClick={toggleTheme}
            className={styles.themeToggle}
            aria-label={`切换到${theme === 'light' ? '深色' : '浅色'}主题`}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
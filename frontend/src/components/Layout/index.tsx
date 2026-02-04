import React from 'react';
import Header from '@/components/Header';
import styles from './index.module.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className={styles.layout}>
      <Header />
      <main className={styles.main}>
        {children}
      </main>
    </div>
  );
};

export default Layout;
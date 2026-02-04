import { Link } from 'react-router-dom';
import styles from './index.module.css';

function NotFoundPage() {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <h1 className={styles.title}>404</h1>
        <h2 className={styles.subtitle}>页面未找到</h2>
        <p className={styles.message}>
          抱歉，您访问的页面不存在。
        </p>
        <Link to="/" className={styles.homeLink}>
          返回首页
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
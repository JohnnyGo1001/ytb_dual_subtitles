import { useToast } from '@/contexts/ToastContext';
import styles from './index.module.css';

function ToastItem({ toast, onClose }: {
  toast: { id: string; type: 'success' | 'error' | 'warning' | 'info'; title: string; message?: string },
  onClose: (id: string) => void
}) {
  return (
    <div className={`${styles.toast} ${styles[toast.type]}`}>
      <div className={styles.content}>
        <div className={styles.title}>{toast.title}</div>
        {toast.message && <div className={styles.message}>{toast.message}</div>}
      </div>
      <button
        className={styles.closeButton}
        onClick={() => onClose(toast.id)}
        aria-label="Close notification"
      >
        ×
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className={styles.container}>
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={removeToast}
        />
      ))}
    </div>
  );
}
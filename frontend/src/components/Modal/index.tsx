import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import styles from './index.module.css';

export interface ModalProps {
  /** 是否显示模态框 */
  isOpen: boolean;
  /** 关闭回调函数 */
  onClose: () => void;
  /** 模态框标题 */
  title: string;
  /** 模态框尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 底部内容 */
  footer?: React.ReactNode;
  /** 隐藏关闭按钮 */
  hideCloseButton?: boolean;
  /** 子元素 */
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'medium',
  footer,
  hideCloseButton = false,
  children,
}) => {
  // 处理ESC键关闭
  const handleEscapeKey = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  // 处理点击遮罩层关闭
  const handleOverlayClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  // 阻止模态框内容点击事件冒泡
  const handleContentClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
  }, []);

  // 设置键盘监听
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      // 阻止背景滚动
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleEscapeKey);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, handleEscapeKey]);

  if (!isOpen) {
    return null;
  }

  const modal = (
    <div
      className={styles.overlay}
      onClick={handleOverlayClick}
      data-testid="modal-overlay"
    >
      <div
        className={clsx(styles.modal, styles[size])}
        onClick={handleContentClick}
        data-testid="modal-content"
      >
        <div className={styles.header}>
          <h2 className={styles.title}>{title}</h2>
          {!hideCloseButton && (
            <button
              className={styles.closeButton}
              onClick={onClose}
              data-testid="modal-close"
              aria-label="Close modal"
            >
              ✕
            </button>
          )}
        </div>

        <div className={styles.body}>{children}</div>

        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );

  // 使用Portal渲染到body
  return createPortal(modal, document.body);
};

export default Modal;
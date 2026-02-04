import React from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import styles from './index.module.css';

export interface LoadingProps {
  /** 加载文本 */
  text?: string;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 是否显示为覆盖层 */
  overlay?: boolean;
  /** 是否居中显示 */
  centered?: boolean;
  /** 自定义样式类 */
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  text,
  size = 'medium',
  overlay = false,
  centered = false,
  className,
}) => {
  const spinner = (
    <div
      className={clsx(styles.spinner, styles[size])}
      data-testid="loading-spinner"
    />
  );

  const content = (
    <div
      className={clsx(
        styles.container,
        {
          [styles.centered]: centered && !overlay,
        },
        className
      )}
      data-testid="loading-container"
    >
      {spinner}
      {text && <span className={styles.text}>{text}</span>}
    </div>
  );

  if (overlay) {
    const overlayContent = (
      <div className={styles.overlay} data-testid="loading-overlay">
        <div className={styles.overlayContent}>
          {spinner}
          {text && <span className={styles.text}>{text}</span>}
        </div>
      </div>
    );

    return createPortal(overlayContent, document.body);
  }

  return content;
};

export default Loading;
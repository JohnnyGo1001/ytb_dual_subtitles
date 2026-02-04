import React from 'react';
import clsx from 'clsx';
import styles from './index.module.css';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** 按钮变体 */
  variant?: 'primary' | 'secondary' | 'danger';
  /** 按钮尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 加载状态 */
  loading?: boolean;
  /** 子元素 */
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  className,
  children,
  ...props
}) => {
  const isDisabled = disabled || loading;

  return (
    <button
      className={clsx(
        styles.button,
        styles[variant],
        styles[size],
        {
          [styles.disabled]: isDisabled,
          [styles.loading]: loading,
        },
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <div
          className={styles.loadingSpinner}
          data-testid="loading-spinner"
        />
      )}
      {children}
    </button>
  );
};

export default Button;
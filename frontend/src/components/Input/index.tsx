import React from 'react';
import clsx from 'clsx';
import styles from './index.module.css';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'prefix'> {
  /** 标签文本 */
  label?: string;
  /** 错误信息 */
  error?: string;
  /** 输入框尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 前缀图标或文本 */
  prefix?: React.ReactNode;
  /** 后缀图标或文本 */
  suffix?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  size = 'medium',
  prefix,
  suffix,
  disabled = false,
  className,
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div
      className={clsx(
        styles.inputContainer,
        styles[size],
        {
          [styles.error]: error,
          [styles.disabled]: disabled,
        }
      )}
    >
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}

      <div className={styles.inputWrapper}>
        {prefix && <div className={styles.prefix}>{prefix}</div>}

        <input
          id={inputId}
          className={clsx(
            styles.input,
            styles[size],
            {
              [styles.error]: error,
              [styles.disabled]: disabled,
            },
            className
          )}
          disabled={disabled}
          {...props}
        />

        {suffix && <div className={styles.suffix}>{suffix}</div>}
      </div>

      {error && <div className={styles.errorMessage}>{error}</div>}
    </div>
  );
};

export default Input;
import { useState, useEffect, useRef } from 'react';
import styles from './index.module.css';

interface Category {
  id: number;
  name: string;
  icon?: string;
  color?: string;
}

interface CategorySelectorProps {
  currentCategory: string;
  onSelect: (category: string) => void;
  onClose: () => void;
}

export function CategorySelector({ currentCategory, onSelect, onClose }: CategorySelectorProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load categories
    const loadCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/categories');
        const result = await response.json();
        if (result.success && result.data) {
          setCategories(result.data.categories);
        }
      } catch (error) {
        console.error('Failed to load categories:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCategories();
  }, []);

  useEffect(() => {
    // Close on click outside
    const handleClickOutside = (event: MouseEvent) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const handleSelect = (categoryName: string) => {
    onSelect(categoryName);
    onClose();
  };

  return (
    <div className={styles.selector} ref={selectorRef}>
      <div className={styles.header}>选择分类</div>
      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : (
        <div className={styles.list}>
          {categories.map((category) => (
            <button
              key={category.id}
              className={`${styles.item} ${category.name === currentCategory ? styles.active : ''}`}
              onClick={() => handleSelect(category.name)}
            >
              <span
                className={styles.colorDot}
                style={{ backgroundColor: category.color }}
              />
              <span className={styles.icon}>{category.icon}</span>
              <span className={styles.name}>{category.name}</span>
              {category.name === currentCategory && (
                <span className={styles.checkmark}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

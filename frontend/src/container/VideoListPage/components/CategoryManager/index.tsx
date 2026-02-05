import { useState, useEffect } from 'react';
import { useApi } from '@/hooks/useApi';
import { apiService } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';
import styles from './index.module.css';

interface Category {
  id: number;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order: number;
  is_system: boolean;
  video_count: number;
}

interface CategoryManagerProps {
  onClose: () => void;
  onCategoryUpdate: () => void;
}

export function CategoryManager({ onClose, onCategoryUpdate }: CategoryManagerProps) {
  const { showToast } = useToast();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#3B82F6',
    icon: '📁',
  });

  // Load categories
  const loadCategories = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getCategories();
      if (response.success && response.data) {
        setCategories(response.data.categories);
      }
    } catch (error) {
      showToast('加载分类失败', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      showToast('请输入分类名称', 'warning');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        showToast('分类创建成功', 'success');
        setIsCreating(false);
        setFormData({ name: '', description: '', color: '#3B82F6', icon: '📁' });
        loadCategories();
        onCategoryUpdate();
      } else {
        showToast(result.error_msg || '创建失败', 'error');
      }
    } catch (error) {
      showToast('创建分类失败', 'error');
    }
  };

  const handleUpdate = async (categoryId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/categories/${categoryId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        showToast('分类更新成功', 'success');
        setEditingId(null);
        setFormData({ name: '', description: '', color: '#3B82F6', icon: '📁' });
        loadCategories();
        onCategoryUpdate();
      } else {
        showToast(result.error_msg || '更新失败', 'error');
      }
    } catch (error) {
      showToast('更新分类失败', 'error');
    }
  };

  const handleDelete = async (categoryId: number, categoryName: string) => {
    if (!window.confirm(`确定要删除分类 "${categoryName}" 吗？\n该分类下的视频将移动到"未分类"。`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/categories/${categoryId}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (result.success) {
        showToast('分类删除成功', 'success');
        loadCategories();
        onCategoryUpdate();
      } else {
        showToast(result.error_msg || '删除失败', 'error');
      }
    } catch (error) {
      showToast('删除分类失败', 'error');
    }
  };

  const startEdit = (category: Category) => {
    setEditingId(category.id);
    setFormData({
      name: category.name,
      description: category.description || '',
      color: category.color || '#3B82F6',
      icon: category.icon || '📁',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setIsCreating(false);
    setFormData({ name: '', description: '', color: '#3B82F6', icon: '📁' });
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>分类管理</h2>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>

        <div className={styles.content}>
          {/* Create New Category */}
          {!isCreating && !editingId && (
            <button className={styles.createButton} onClick={() => setIsCreating(true)}>
              ➕ 创建新分类
            </button>
          )}

          {/* Create Form */}
          {isCreating && (
            <div className={styles.form}>
              <h3>创建新分类</h3>
              <div className={styles.formRow}>
                <label>图标</label>
                <input
                  type="text"
                  value={formData.icon}
                  onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                  placeholder="📁"
                  maxLength={2}
                />
              </div>
              <div className={styles.formRow}>
                <label>名称 *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="分类名称"
                />
              </div>
              <div className={styles.formRow}>
                <label>描述</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="分类描述"
                />
              </div>
              <div className={styles.formRow}>
                <label>颜色</label>
                <input
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                />
              </div>
              <div className={styles.formActions}>
                <button className={styles.saveButton} onClick={handleCreate}>保存</button>
                <button className={styles.cancelButton} onClick={cancelEdit}>取消</button>
              </div>
            </div>
          )}

          {/* Category List */}
          {isLoading ? (
            <div className={styles.loading}>加载中...</div>
          ) : (
            <div className={styles.categoryList}>
              {categories.map((category) => (
                <div key={category.id} className={styles.categoryItem}>
                  {editingId === category.id ? (
                    // Edit Form
                    <div className={styles.form}>
                      <h3>编辑分类</h3>
                      <div className={styles.formRow}>
                        <label>图标</label>
                        <input
                          type="text"
                          value={formData.icon}
                          onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                          maxLength={2}
                        />
                      </div>
                      <div className={styles.formRow}>
                        <label>名称 *</label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        />
                      </div>
                      <div className={styles.formRow}>
                        <label>描述</label>
                        <input
                          type="text"
                          value={formData.description}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        />
                      </div>
                      <div className={styles.formRow}>
                        <label>颜色</label>
                        <input
                          type="color"
                          value={formData.color}
                          onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                        />
                      </div>
                      <div className={styles.formActions}>
                        <button className={styles.saveButton} onClick={() => handleUpdate(category.id)}>
                          保存
                        </button>
                        <button className={styles.cancelButton} onClick={cancelEdit}>取消</button>
                      </div>
                    </div>
                  ) : (
                    // Display Category
                    <div className={styles.categoryInfo}>
                      <div className={styles.categoryHeader}>
                        <span
                          className={styles.categoryColor}
                          style={{ backgroundColor: category.color }}
                        />
                        <span className={styles.categoryIcon}>{category.icon}</span>
                        <div className={styles.categoryDetails}>
                          <div className={styles.categoryName}>{category.name}</div>
                          <div className={styles.categoryDescription}>{category.description}</div>
                        </div>
                        <div className={styles.categoryCount}>{category.video_count} 个视频</div>
                      </div>
                      <div className={styles.categoryActions}>
                        <button
                          className={styles.editButton}
                          onClick={() => startEdit(category)}
                          disabled={category.is_system}
                        >
                          编辑
                        </button>
                        <button
                          className={styles.deleteButton}
                          onClick={() => handleDelete(category.id, category.name)}
                          disabled={category.is_system}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

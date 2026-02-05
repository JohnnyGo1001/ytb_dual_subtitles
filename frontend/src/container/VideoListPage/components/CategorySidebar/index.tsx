import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { useToast } from '@/contexts/ToastContext';
import styles from './index.module.css';

interface Category {
  id: string;
  name: string;
  video_count: number;
}

interface CategorySidebarProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  onCategoriesChange: () => void;
}

const CategorySidebar: React.FC<CategorySidebarProps> = ({
  selectedCategory,
  onSelectCategory,
  onCategoriesChange,
}) => {
  const { showToast } = useToast();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [editingCategoryName, setEditingCategoryName] = useState('');
  const [totalVideoCount, setTotalVideoCount] = useState(0);

  // Load categories
  const loadCategories = async () => {
    try {
      const response = await apiService.getCategories();
      if (response.success && response.data) {
        // API returns {categories: [...], total: number}
        const categoriesData = response.data.categories || [];
        setCategories(categoriesData);

        // Calculate total video count
        const total = categoriesData.reduce((sum: number, cat: Category) => sum + cat.video_count, 0);
        setTotalVideoCount(total);
      }
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  // Add new category
  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) {
      showToast('分类名称不能为空', 'warning');
      return;
    }

    try {
      const response = await apiService.createCategory({ name: newCategoryName.trim() });
      if (response.success) {
        showToast('分类创建成功', 'success');
        setNewCategoryName('');
        setIsAddingCategory(false);
        loadCategories();
        onCategoriesChange();
      } else {
        showToast(response.error_msg || '创建分类失败', 'error');
      }
    } catch (error) {
      showToast('创建分类失败', 'error');
    }
  };

  // Start editing category
  const handleStartEdit = (category: Category) => {
    setEditingCategoryId(category.id);
    setEditingCategoryName(category.name);
  };

  // Save edited category
  const handleSaveEdit = async (categoryId: string) => {
    if (!editingCategoryName.trim()) {
      showToast('分类名称不能为空', 'warning');
      return;
    }

    try {
      const response = await apiService.updateCategory(Number(categoryId), { name: editingCategoryName.trim() });
      if (response.success) {
        showToast('分类更新成功', 'success');
        setEditingCategoryId(null);
        setEditingCategoryName('');
        loadCategories();
        onCategoriesChange();
      } else {
        showToast(response.error_msg || '更新分类失败', 'error');
      }
    } catch (error) {
      showToast('更新分类失败', 'error');
    }
  };

  // Delete category
  const handleDeleteCategory = async (categoryId: string, categoryName: string) => {
    if (!window.confirm(`确定要删除分类 "${categoryName}" 吗？该分类下的视频将被移至"未分类"。`)) {
      return;
    }

    try {
      const response = await apiService.deleteCategory(Number(categoryId));
      if (response.success) {
        showToast('分类删除成功', 'success');
        loadCategories();
        onCategoriesChange();
        if (selectedCategory === categoryName) {
          onSelectCategory('全部');
        }
      } else {
        showToast(response.error_msg || '删除分类失败', 'error');
      }
    } catch (error) {
      showToast('删除分类失败', 'error');
    }
  };

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <h3 className={styles.title}>分类</h3>
      </div>

      <div className={styles.categoryList}>
        {/* 全部分类 */}
        <div
          className={`${styles.categoryItem} ${selectedCategory === '全部' ? styles.active : ''}`}
          onClick={() => onSelectCategory('全部')}
        >
          <span className={styles.categoryName}>📂 全部</span>
          <span className={styles.categoryCount}>{totalVideoCount}</span>
        </div>

        {/* 其他分类 */}
        {categories.map((category) => (
          <div key={category.id} className={styles.categoryWrapper}>
            {editingCategoryId === category.id ? (
              // 编辑模式
              <div className={styles.editMode}>
                <input
                  type="text"
                  value={editingCategoryName}
                  onChange={(e) => setEditingCategoryName(e.target.value)}
                  className={styles.editInput}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveEdit(category.id);
                    } else if (e.key === 'Escape') {
                      setEditingCategoryId(null);
                    }
                  }}
                />
                <button
                  className={styles.saveButton}
                  onClick={() => handleSaveEdit(category.id)}
                  title="保存"
                >
                  ✓
                </button>
                <button
                  className={styles.cancelButton}
                  onClick={() => setEditingCategoryId(null)}
                  title="取消"
                >
                  ✕
                </button>
              </div>
            ) : (
              // 正常显示模式
              <div
                className={`${styles.categoryItem} ${selectedCategory === category.name ? styles.active : ''}`}
                onClick={() => onSelectCategory(category.name)}
              >
                <span className={styles.categoryName}>🏷️ {category.name}</span>
                <div className={styles.categoryActions}>
                  <span className={styles.categoryCount}>{category.video_count}</span>
                  <button
                    className={styles.editButton}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(category);
                    }}
                    title="编辑分类"
                  >
                    ✏️
                  </button>
                  <button
                    className={styles.deleteButton}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteCategory(category.id, category.name);
                    }}
                    title="删除分类"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 添加分类 */}
      <div className={styles.addCategory}>
        {isAddingCategory ? (
          <div className={styles.addCategoryForm}>
            <input
              type="text"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="输入分类名称"
              className={styles.addInput}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAddCategory();
                } else if (e.key === 'Escape') {
                  setIsAddingCategory(false);
                  setNewCategoryName('');
                }
              }}
            />
            <button
              className={styles.saveButton}
              onClick={handleAddCategory}
              title="添加"
            >
              ✓
            </button>
            <button
              className={styles.cancelButton}
              onClick={() => {
                setIsAddingCategory(false);
                setNewCategoryName('');
              }}
              title="取消"
            >
              ✕
            </button>
          </div>
        ) : (
          <button
            className={styles.addButton}
            onClick={() => setIsAddingCategory(true)}
          >
            ➕ 添加分类
          </button>
        )}
      </div>
    </div>
  );
};

export default CategorySidebar;

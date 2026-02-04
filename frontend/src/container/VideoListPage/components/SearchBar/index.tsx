import React, { useState } from 'react';
import Button from '@/components/Button';
import Input from '@/components/Input';
import styles from './index.module.css';

export type SortField = 'created_at' | 'title' | 'duration' | 'view_count';
export type SortOrder = 'asc' | 'desc';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onSort: (field: SortField, order: SortOrder) => void;
  searchQuery: string;
  sortBy: SortField;
  sortOrder: SortOrder;
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onSort,
  searchQuery,
  sortBy,
  sortOrder,
}) => {
  const [inputValue, setInputValue] = useState(searchQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(inputValue);
  };

  const handleSortChange = (field: SortField) => {
    const newOrder = sortBy === field && sortOrder === 'desc' ? 'asc' : 'desc';
    onSort(field, newOrder);
  };

  return (
    <div className={styles.searchBar}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <div className={styles.searchInput}>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="搜索视频标题..."
            className={styles.input}
          />
          <Button type="submit" className={styles.searchButton}>
            搜索
          </Button>
        </div>
      </form>

      <div className={styles.sortControls}>
        <span className={styles.sortLabel}>排序:</span>
        <button
          className={`${styles.sortButton} ${sortBy === 'created_at' ? styles.active : ''}`}
          onClick={() => handleSortChange('created_at')}
        >
          创建时间 {sortBy === 'created_at' && (sortOrder === 'desc' ? '↓' : '↑')}
        </button>
        <button
          className={`${styles.sortButton} ${sortBy === 'title' ? styles.active : ''}`}
          onClick={() => handleSortChange('title')}
        >
          标题 {sortBy === 'title' && (sortOrder === 'desc' ? '↓' : '↑')}
        </button>
        <button
          className={`${styles.sortButton} ${sortBy === 'duration' ? styles.active : ''}`}
          onClick={() => handleSortChange('duration')}
        >
          时长 {sortBy === 'duration' && (sortOrder === 'desc' ? '↓' : '↑')}
        </button>
        <button
          className={`${styles.sortButton} ${sortBy === 'view_count' ? styles.active : ''}`}
          onClick={() => handleSortChange('view_count')}
        >
          播放量 {sortBy === 'view_count' && (sortOrder === 'desc' ? '↓' : '↑')}
        </button>
      </div>
    </div>
  );
};

export default SearchBar;
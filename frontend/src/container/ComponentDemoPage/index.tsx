import React, { useState } from 'react';
import Button from '@/components/Button';
import Input from '@/components/Input';
import Modal from '@/components/Modal';
import Loading from '@/components/Loading';
import styles from './index.module.css';

export const ComponentDemoPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const handleLoadingDemo = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 3000);
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>通用组件演示</h1>

      {/* Button演示 */}
      <section className={styles.section}>
        <h2>Button 按钮组件</h2>
        <div className={styles.buttonGroup}>
          <Button variant="primary">主要按钮</Button>
          <Button variant="secondary">次要按钮</Button>
          <Button variant="danger">危险按钮</Button>
          <Button disabled>禁用按钮</Button>
          <Button loading>加载中</Button>
        </div>
        <div className={styles.buttonGroup}>
          <Button size="small">小按钮</Button>
          <Button size="medium">中按钮</Button>
          <Button size="large">大按钮</Button>
        </div>
      </section>

      {/* Input演示 */}
      <section className={styles.section}>
        <h2>Input 输入框组件</h2>
        <div className={styles.inputGroup}>
          <Input
            label="用户名"
            placeholder="请输入用户名"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <Input
            label="搜索"
            placeholder="输入关键词..."
            prefix={<span>🔍</span>}
          />
          <Input
            label="密码"
            type="password"
            placeholder="请输入密码"
            error="密码长度至少6位"
          />
          <Input
            disabled
            placeholder="禁用状态"
          />
        </div>
      </section>

      {/* Modal演示 */}
      <section className={styles.section}>
        <h2>Modal 模态框组件</h2>
        <div className={styles.buttonGroup}>
          <Button onClick={() => setIsModalOpen(true)}>打开模态框</Button>
          <Button onClick={handleLoadingDemo}>显示加载覆盖层</Button>
        </div>
      </section>

      {/* Loading演示 */}
      <section className={styles.section}>
        <h2>Loading 加载组件</h2>
        <div className={styles.loadingGroup}>
          <Loading size="small" text="小尺寸" />
          <Loading size="medium" text="中尺寸" />
          <Loading size="large" text="大尺寸" />
        </div>
        <Loading centered text="居中显示的加载状态" />
      </section>

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="演示模态框"
        size="medium"
        footer={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              取消
            </Button>
            <Button onClick={() => setIsModalOpen(false)}>
              确认
            </Button>
          </div>
        }
      >
        <p>这是一个演示模态框的内容。</p>
        <p>可以点击遮罩层或按ESC键关闭。</p>
      </Modal>

      {/* Loading覆盖层 */}
      {isLoading && (
        <Loading overlay text="正在处理，请稍候..." />
      )}
    </div>
  );
};

export default ComponentDemoPage;
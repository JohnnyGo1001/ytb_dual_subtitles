import React, { useState } from 'react';
import { useUnifiedApi } from '@/hooks/useUnifiedApi';
import { apiService } from '@/services/api';
import type { DownloadTaskData, VideoListData } from '@/types/apiResponse';

/**
 * API使用示例组件
 * 演示如何正确使用新的统一API响应格式
 */
export const ApiExample: React.FC = () => {
  const [url, setUrl] = useState('');

  // 使用统一API Hook
  const {
    data: downloadData,
    isLoading: downloadLoading,
    error: downloadError,
    execute: executeDownload,
  } = useUnifiedApi<DownloadTaskData>();

  const {
    data: videosData,
    isLoading: videosLoading,
    error: videosError,
    execute: executeGetVideos,
  } = useUnifiedApi<VideoListData>();

  // 创建下载任务的示例
  const handleCreateDownload = async () => {
    if (!url) return;

    const result = await executeDownload(async () => {
      return await apiService.createDownload({ url });
    });

    if (result) {
      console.log('下载任务创建成功:', result);
    }
  };

  // 获取视频列表的示例
  const handleGetVideos = async () => {
    const result = await executeGetVideos(async () => {
      return await apiService.getVideos(1, 10);
    });

    if (result) {
      console.log('视频列表获取成功:', result);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h2>API使用示例</h2>

      {/* 下载示例 */}
      <div style={{ marginBottom: '20px' }}>
        <h3>创建下载任务</h3>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="输入YouTube URL"
          style={{ width: '300px', marginRight: '10px' }}
        />
        <button
          onClick={handleCreateDownload}
          disabled={downloadLoading || !url}
        >
          {downloadLoading ? '创建中...' : '创建下载'}
        </button>

        {downloadError && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            错误: {downloadError}
          </div>
        )}

        {downloadData && (
          <div style={{ marginTop: '10px' }}>
            <h4>下载任务信息:</h4>
            <pre>{JSON.stringify(downloadData, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* 视频列表示例 */}
      <div>
        <h3>获取视频列表</h3>
        <button
          onClick={handleGetVideos}
          disabled={videosLoading}
        >
          {videosLoading ? '加载中...' : '获取视频列表'}
        </button>

        {videosError && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            错误: {videosError}
          </div>
        )}

        {videosData && (
          <div style={{ marginTop: '10px' }}>
            <h4>视频列表 ({videosData.videos.length} 个视频):</h4>
            {videosData.videos.map((video) => (
              <div key={video.id} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #ccc' }}>
                <strong>{video.title}</strong>
                <div>状态: {video.status}</div>
                <div>创建时间: {video.created_at}</div>
              </div>
            ))}

            <h4>分页信息:</h4>
            <div>页码: {videosData.pagination.page}/{videosData.pagination.total_pages}</div>
            <div>总数: {videosData.pagination.total}</div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f5f5f5' }}>
        <h3>使用说明:</h3>
        <ul>
          <li>所有API响应都有统一格式: <code>{`{success, data, error_code, error_msg}`}</code></li>
          <li>成功时 <code>success</code> 为 <code>true</code>，数据在 <code>data</code> 字段</li>
          <li>失败时 <code>success</code> 为 <code>false</code>，错误信息在 <code>error_msg</code> 字段</li>
          <li>错误码在 <code>error_code</code> 字段，可用于程序化处理</li>
          <li>Hook会自动处理错误格式化和用户友好的提示</li>
        </ul>
      </div>
    </div>
  );
};

export default ApiExample;
/**
 * YouTube URL 验证函数
 */
export function isValidYouTubeURL(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  // YouTube URL 正则表达式
  const youtubeRegex = /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})(?:\S+)?$/;

  return youtubeRegex.test(url.trim());
}

/**
 * 提取YouTube视频ID
 */
export function extractYouTubeVideoId(url: string): string | null {
  if (!isValidYouTubeURL(url)) {
    return null;
  }

  const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})/;
  const match = url.match(regex);

  return match ? match[1] : null;
}

/**
 * 验证视频质量选项
 */
export function isValidVideoQuality(quality: string): boolean {
  const validQualities = ['best', 'worst', 'bestvideo', 'bestaudio'];
  return validQualities.includes(quality);
}

/**
 * 验证视频格式
 */
export function isValidVideoFormat(format: string): boolean {
  const validFormats = ['mp4', 'webm'];
  return validFormats.includes(format);
}

/**
 * 验证分页参数
 */
export function isValidPaginationParams(page: number, size: number): boolean {
  return (
    Number.isInteger(page) &&
    Number.isInteger(size) &&
    page > 0 &&
    size > 0 &&
    size <= 100 // 限制单页最大数量
  );
}

/**
 * 验证搜索关键词
 */
export function isValidSearchQuery(query: string): boolean {
  if (!query || typeof query !== 'string') {
    return false;
  }

  const trimmed = query.trim();
  return trimmed.length >= 1 && trimmed.length <= 100;
}

/**
 * 验证视频ID格式
 */
export function isValidVideoId(id: string): boolean {
  if (!id || typeof id !== 'string') {
    return false;
  }

  // 假设视频ID是UUID格式或YouTube ID格式
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const youtubeIdRegex = /^[a-zA-Z0-9_-]{11}$/;

  return uuidRegex.test(id) || youtubeIdRegex.test(id);
}

/**
 * 清理和验证表单输入
 */
export function sanitizeInput(input: string): string {
  return input.trim().replace(/[\r\n\t]/g, ' ').substring(0, 1000);
}

/**
 * 验证文件大小（字节）
 */
export function isValidFileSize(size: number, maxSizeGB = 10): boolean {
  const maxSizeBytes = maxSizeGB * 1024 * 1024 * 1024; // 转换为字节
  return size > 0 && size <= maxSizeBytes;
}
"""字幕工具函数

Task 6: 字幕工具函数和格式转换 (AC: 6)
提供字幕格式转换、文本处理、质量检查等工具函数
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class SubtitleUtils:
    """字幕处理工具类 - 提供格式转换和文本处理功能"""

    @staticmethod
    def format_time_to_srt(seconds: float) -> str:
        """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)

        Args:
            seconds: 时间（秒）

        Returns:
            SRT格式时间字符串

        Example:
            >>> SubtitleUtils.format_time_to_srt(3661.5)
            '01:01:01,500'
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    def parse_srt_time(time_str: str) -> float:
        """解析SRT时间格式为秒数

        Args:
            time_str: SRT格式时间字符串

        Returns:
            秒数

        Example:
            >>> SubtitleUtils.parse_srt_time('01:01:01,500')
            3661.5
        """
        try:
            time_part, ms_part = time_str.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)

            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid SRT time format: {time_str}") from e

    @staticmethod
    def export_to_srt(
        subtitle_data: Dict[str, Any],
        mode: str = "bilingual",
        include_sequence: bool = True
    ) -> str:
        """导出字幕为SRT格式

        Args:
            subtitle_data: 字幕数据字典
            mode: 导出模式 ('bilingual', 'english', 'chinese')
            include_sequence: 是否包含序号

        Returns:
            SRT格式字符串
        """
        if not subtitle_data or 'segments' not in subtitle_data:
            return ""

        srt_content = []
        segments = subtitle_data['segments']

        for i, segment in enumerate(segments, 1):
            start_time = SubtitleUtils.format_time_to_srt(segment.get('start_time', 0))
            end_time = SubtitleUtils.format_time_to_srt(segment.get('end_time', 0))

            # 构建文本内容
            if mode == 'bilingual':
                english = segment.get('english', segment.get('text', ''))
                chinese = segment.get('chinese', '')
                text = f"{english}
{chinese}" if chinese else english
            elif mode == 'english':
                text = segment.get('english', segment.get('text', ''))
            elif mode == 'chinese':
                text = segment.get('chinese', segment.get('text', ''))
            else:
                text = segment.get('text', '')

            # 构建SRT块
            if include_sequence:
                srt_block = f"{i}
{start_time} --> {end_time}
{text}
"
            else:
                srt_block = f"{start_time} --> {end_time}
{text}
"

            srt_content.append(srt_block)

        return "
".join(srt_content)

    @staticmethod
    def clean_subtitle_text(text: str) -> str:
        """清理和标准化字幕文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除特殊字符和控制字符
        text = re.sub(r'[
	]+', ' ', text)

        # 标准化空白字符
        text = ' '.join(text.split())

        # 移除多余的标点符号
        text = re.sub(r'[.]{3,}', '...', text)

        return text.strip()

    @staticmethod
    def normalize_subtitle_text(text: str, max_length: int = 80) -> str:
        """标准化字幕文本格式

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            标准化后的文本
        """
        text = SubtitleUtils.clean_subtitle_text(text)

        # 如果文本太长，尝试在合适位置断行
        if len(text) > max_length:
            # 在句号、逗号等标点符号处断行
            break_points = ['.', ',', ';', '!', '?']
            best_break = -1

            for i in range(max_length - 10, max_length + 10):
                if i < len(text) and text[i] in break_points:
                    best_break = i + 1
                    break

            if best_break > 0:
                text = text[:best_break].strip()

        return text

    @staticmethod
    def validate_subtitle_quality(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证字幕质量

        Args:
            segments: 字幕片段列表

        Returns:
            质量评估结果
        """
        if not segments:
            return {
                'quality_score': 0.0,
                'total_segments': 0,
                'valid_segments': 0,
                'issues': ['No segments found']
            }

        issues = []
        valid_segments = 0
        timing_issues = 0
        text_issues = 0

        for i, segment in enumerate(segments):
            segment_issues = []

            # 检查文本内容
            text = (segment.get('text') or 
                   segment.get('english') or 
                   segment.get('chinese') or '').strip()

            if not text:
                segment_issues.append('Empty text')
                text_issues += 1
            elif len(text) < 3:
                segment_issues.append('Text too short')
                text_issues += 1
            else:
                valid_segments += 1

            # 检查时间有效性
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)

            if start_time >= end_time:
                segment_issues.append('Invalid timing: start >= end')
                timing_issues += 1

            if end_time - start_time < 0.5:
                segment_issues.append('Duration too short')
                timing_issues += 1

            if segment_issues:
                issues.append(f"Segment {i + 1}: {', '.join(segment_issues)}")

        # 检查时间重叠
        for i in range(len(segments) - 1):
            current_end = segments[i].get('end_time', 0)
            next_start = segments[i + 1].get('start_time', 0)

            if current_end > next_start:
                issues.append(f"Timing overlap between segments {i + 1} and {i + 2}")
                timing_issues += 1

        quality_score = valid_segments / len(segments) if segments else 0.0

        return {
            'quality_score': quality_score,
            'total_segments': len(segments),
            'valid_segments': valid_segments,
            'timing_issues': timing_issues,
            'text_issues': text_issues,
            'issues': issues[:10]  # 限制显示的问题数量
        }

    @staticmethod
    def merge_subtitle_segments(
        segments: List[Dict[str, Any]],
        max_gap: float = 0.5,
        max_duration: float = 6.0
    ) -> List[Dict[str, Any]]:
        """合并相邻的字幕片段

        Args:
            segments: 字幕片段列表
            max_gap: 最大间隙时间（秒）
            max_duration: 合并后的最大持续时间（秒）

        Returns:
            合并后的片段列表
        """
        if not segments:
            return []

        merged_segments = []
        current_segment = segments[0].copy()

        for next_segment in segments[1:]:
            gap = next_segment.get('start_time', 0) - current_segment.get('end_time', 0)
            current_duration = current_segment.get('end_time', 0) - current_segment.get('start_time', 0)

            # 检查是否可以合并
            if (gap <= max_gap and 
                current_duration < max_duration and
                current_segment.get('language') == next_segment.get('language')):

                # 合并片段
                current_segment['end_time'] = next_segment.get('end_time', 0)
                
                # 合并文本
                current_text = current_segment.get('text', '')
                next_text = next_segment.get('text', '')
                current_segment['text'] = f"{current_text} {next_text}".strip()

            else:
                # 不能合并，添加当前片段并开始新片段
                merged_segments.append(current_segment)
                current_segment = next_segment.copy()

        # 添加最后一个片段
        merged_segments.append(current_segment)

        # 重新编号
        for i, segment in enumerate(merged_segments):
            segment['sequence'] = i + 1

        return merged_segments

    @staticmethod
    def split_long_segments(
        segments: List[Dict[str, Any]],
        max_duration: float = 5.0,
        max_chars: int = 100
    ) -> List[Dict[str, Any]]:
        """拆分过长的字幕片段

        Args:
            segments: 字幕片段列表
            max_duration: 最大持续时间（秒）
            max_chars: 最大字符数

        Returns:
            拆分后的片段列表
        """
        if not segments:
            return []

        split_segments = []

        for segment in segments:
            duration = segment.get('end_time', 0) - segment.get('start_time', 0)
            text = segment.get('text', '')

            # 检查是否需要拆分
            if duration <= max_duration and len(text) <= max_chars:
                split_segments.append(segment)
                continue

            # 需要拆分
            words = text.split()
            if len(words) <= 1:
                # 无法拆分，保持原样
                split_segments.append(segment)
                continue

            # 拆分为两个片段
            mid_point = len(words) // 2
            first_text = ' '.join(words[:mid_point])
            second_text = ' '.join(words[mid_point:])

            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            mid_time = start_time + duration / 2

            # 第一个片段
            first_segment = segment.copy()
            first_segment.update({
                'end_time': mid_time,
                'text': first_text
            })

            # 第二个片段
            second_segment = segment.copy()
            second_segment.update({
                'start_time': mid_time,
                'text': second_text
            })

            split_segments.extend([first_segment, second_segment])

        # 重新编号
        for i, segment in enumerate(split_segments):
            segment['sequence'] = i + 1

        return split_segments

    @staticmethod
    def calculate_reading_speed(segments: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算字幕阅读速度统计

        Args:
            segments: 字幕片段列表

        Returns:
            阅读速度统计
        """
        if not segments:
            return {
                'characters_per_second': 0.0,
                'words_per_minute': 0.0,
                'average_segment_duration': 0.0
            }

        total_chars = 0
        total_words = 0
        total_duration = 0.0

        for segment in segments:
            text = segment.get('text', '')
            duration = segment.get('end_time', 0) - segment.get('start_time', 0)

            total_chars += len(text)
            total_words += len(text.split())
            total_duration += duration

        if total_duration == 0:
            return {
                'characters_per_second': 0.0,
                'words_per_minute': 0.0,
                'average_segment_duration': 0.0
            }

        return {
            'characters_per_second': total_chars / total_duration,
            'words_per_minute': (total_words / total_duration) * 60,
            'average_segment_duration': total_duration / len(segments)
        }

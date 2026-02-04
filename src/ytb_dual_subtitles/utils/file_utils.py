"""File utility functions for YouTube dual-subtitles system.

This module provides secure file operations, validation and logging utilities.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any

from ytb_dual_subtitles.exceptions.file_errors import FileOperationError, FileErrorCode

logger = logging.getLogger(__name__)


def safe_delete_file(file_path: Path, log_operation: bool = True) -> bool:
    """Safely delete a file with proper validation and logging.

    Args:
        file_path: Path to file to delete
        log_operation: Whether to log the operation

    Returns:
        True if file was deleted successfully, False otherwise

    Raises:
        FileOperationError: If operation fails due to permissions or other errors
    """
    if not file_path.exists():
        if log_operation:
            logger.warning(f"Cannot delete non-existent file: {file_path}")
        return False

    if not file_path.is_file():
        raise FileOperationError(
            f"Path is not a file: {file_path}",
            FileErrorCode.INVALID_FILE_TYPE
        )

    try:
        file_path.unlink()
        if log_operation:
            logger.info(f"Successfully deleted file: {file_path}")
        return True

    except PermissionError as e:
        raise FileOperationError(
            f"Permission denied deleting file: {file_path}",
            FileErrorCode.PERMISSION_DENIED
        ) from e
    except OSError as e:
        raise FileOperationError(
            f"OS error deleting file: {file_path} - {e}",
            FileErrorCode.PERMISSION_DENIED
        ) from e


def safe_move_file(src_path: Path, dst_path: Path, log_operation: bool = True) -> bool:
    """Safely move a file with validation and logging.

    Args:
        src_path: Source file path
        dst_path: Destination file path
        log_operation: Whether to log the operation

    Returns:
        True if file was moved successfully, False otherwise

    Raises:
        FileOperationError: If operation fails
    """
    if not src_path.exists():
        raise FileOperationError(
            f"Source file does not exist: {src_path}",
            FileErrorCode.FILE_NOT_FOUND
        )

    if dst_path.exists():
        raise FileOperationError(
            f"Destination file already exists: {dst_path}",
            FileErrorCode.INVALID_FILE_TYPE
        )

    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(str(src_path), str(dst_path))
        if log_operation:
            logger.info(f"Successfully moved file: {src_path} -> {dst_path}")
        return True

    except PermissionError as e:
        raise FileOperationError(
            f"Permission denied moving file: {src_path} -> {dst_path}",
            FileErrorCode.PERMISSION_DENIED
        ) from e
    except OSError as e:
        raise FileOperationError(
            f"OS error moving file: {src_path} -> {dst_path} - {e}",
            FileErrorCode.PERMISSION_DENIED
        ) from e


def safe_rename_file(file_path: Path, new_name: str, log_operation: bool = True) -> Path:
    """Safely rename a file with validation.

    Args:
        file_path: Path to file to rename
        new_name: New filename
        log_operation: Whether to log the operation

    Returns:
        New file path after rename

    Raises:
        FileOperationError: If operation fails
    """
    if not file_path.exists():
        raise FileOperationError(
            f"File does not exist: {file_path}",
            FileErrorCode.FILE_NOT_FOUND
        )

    # Validate new filename
    if not is_valid_filename(new_name):
        raise FileOperationError(
            f"Invalid filename: {new_name}",
            FileErrorCode.INVALID_FILE_TYPE
        )

    new_path = file_path.parent / new_name

    if new_path.exists():
        raise FileOperationError(
            f"File with new name already exists: {new_path}",
            FileErrorCode.INVALID_FILE_TYPE
        )

    try:
        file_path.rename(new_path)
        if log_operation:
            logger.info(f"Successfully renamed file: {file_path} -> {new_path}")
        return new_path

    except PermissionError as e:
        raise FileOperationError(
            f"Permission denied renaming file: {file_path} -> {new_path}",
            FileErrorCode.PERMISSION_DENIED
        ) from e
    except OSError as e:
        raise FileOperationError(
            f"OS error renaming file: {file_path} -> {new_path} - {e}",
            FileErrorCode.PERMISSION_DENIED
        ) from e


def calculate_file_hash(file_path: Path, algorithm: str = "md5", chunk_size: int = 8192) -> str:
    """Calculate hash of file content.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        chunk_size: Size of chunks to read

    Returns:
        Hash as hexadecimal string

    Raises:
        FileOperationError: If file cannot be read or hash fails
    """
    if not file_path.exists():
        raise FileOperationError(
            f"File does not exist: {file_path}",
            FileErrorCode.FILE_NOT_FOUND
        )

    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    except (OSError, PermissionError) as e:
        raise FileOperationError(
            f"Cannot read file for hashing: {file_path} - {e}",
            FileErrorCode.PERMISSION_DENIED
        ) from e
    except ValueError as e:
        raise FileOperationError(
            f"Invalid hash algorithm: {algorithm}",
            FileErrorCode.INVALID_FILE_TYPE
        ) from e


def compare_files_by_hash(file1: Path, file2: Path) -> bool:
    """Compare two files by their MD5 hash.

    Args:
        file1: First file path
        file2: Second file path

    Returns:
        True if files have same content, False otherwise
    """
    try:
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        return hash1 == hash2
    except FileOperationError:
        return False


def normalize_filename(filename: str) -> str:
    """Normalize filename by removing unsafe characters and limiting length.

    Args:
        filename: Original filename

    Returns:
        Normalized filename safe for filesystem
    """
    import re

    if not filename or filename.strip() in ("", ".", ".."):
        return "untitled"

    # Remove/replace unsafe characters
    normalized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Replace multiple consecutive underscores with single underscore
    normalized = re.sub(r'_{2,}', '_', normalized)

    # Remove leading/trailing dots and spaces
    normalized = normalized.strip('. ')

    # Limit length to prevent filesystem issues
    if len(normalized) > 200:
        # Try to preserve extension
        if '.' in normalized:
            name, ext = normalized.rsplit('.', 1)
            max_name_len = 200 - len(ext) - 1
            normalized = name[:max_name_len] + '.' + ext
        else:
            normalized = normalized[:200]

    return normalized or "untitled"


def is_valid_filename(filename: str) -> bool:
    """Check if filename contains only safe characters.

    Args:
        filename: Filename to validate

    Returns:
        True if filename is safe, False otherwise
    """
    import re

    if not filename or filename.strip() in ("", ".", ".."):
        return False

    # Check for invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, filename):
        return False

    # Check for reserved names on Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    base_name = filename.split('.')[0].upper()
    if base_name in reserved_names:
        return False

    return True


def check_file_permissions(file_path: Path) -> dict[str, bool]:
    """Check file permissions.

    Args:
        file_path: Path to check

    Returns:
        Dictionary with permission flags
    """
    import os

    permissions = {
        'exists': file_path.exists(),
        'readable': False,
        'writable': False,
        'executable': False,
        'is_file': False,
        'is_dir': False
    }

    if file_path.exists():
        permissions['readable'] = os.access(file_path, os.R_OK)
        permissions['writable'] = os.access(file_path, os.W_OK)
        permissions['executable'] = os.access(file_path, os.X_OK)
        permissions['is_file'] = file_path.is_file()
        permissions['is_dir'] = file_path.is_dir()

    return permissions


def log_file_operation(operation: str, file_path: Path, success: bool, error_msg: str | None = None) -> None:
    """Log a file operation.

    Args:
        operation: Operation name (delete, move, rename, etc.)
        file_path: Path that was operated on
        success: Whether operation succeeded
        error_msg: Error message if operation failed
    """
    if success:
        logger.info(f"File {operation} succeeded: {file_path}")
    else:
        logger.error(f"File {operation} failed: {file_path} - {error_msg or 'Unknown error'}")
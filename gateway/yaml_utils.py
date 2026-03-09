"""Atomic YAML file operations with file locking for thread/process safety."""
import os
import platform
import yaml
import tempfile
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cross-platform file locking
if platform.system() == 'Windows':
    import msvcrt

    def _lock_file(fileno: int, exclusive: bool = False):
        """Windows file locking using msvcrt."""
        try:
            if exclusive:
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
            else:
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
        except OSError:
            pass

    def _unlock_file(fileno: int):
        """Windows file unlocking."""
        try:
            msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock_file(fileno: int, exclusive: bool = False):
        """Unix file locking using fcntl."""
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(fileno, lock_type | fcntl.LOCK_NB)

    def _unlock_file(fileno: int):
        """Unix file unlocking."""
        fcntl.flock(fileno, fcntl.LOCK_UN)


class AtomicYAML:
    """Thread-safe and process-safe atomic YAML file operations."""
    
    @staticmethod
    def load(path: str) -> Optional[Dict[str, Any]]:
        """Load YAML file with shared (read) lock.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Parsed YAML data or None if file doesn't exist
        """
        if not os.path.exists(path):
            return None
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Acquire shared lock for reading (non-blocking)
                _lock_file(f.fileno(), exclusive=False)
                try:
                    content = f.read()
                    if not content.strip():
                        return {}
                    return yaml.safe_load(content) or {}
                finally:
                    _unlock_file(f.fileno())
        except (IOError, OSError) as e:
            logger.error(f"Failed to read {path}: {e}")
            # Fallback: try without locking if flock fails
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e2:
                logger.error(f"Fallback read failed for {path}: {e2}")
                return None
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML {path}: {e}")
            return None
    
    @staticmethod
    def save(path: str, data: Dict[str, Any]) -> bool:
        """Save YAML file atomically with exclusive (write) lock.
        
        Uses write-to-temp-then-rename pattern for atomicity.
        
        Args:
            path: Target path for YAML file
            data: Data to serialize to YAML
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Create temp file in same directory for atomic rename
            fd, temp_path = tempfile.mkstemp(
                dir=dir_path if dir_path else '.',
                prefix='.tmp_',
                suffix='.yaml'
            )
            
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    # Acquire exclusive lock for writing
                    _lock_file(f.fileno(), exclusive=True)
                    try:
                        yaml.dump(
                            data,
                            f,
                            default_flow_style=False,
                            allow_unicode=True,
                            sort_keys=False
                        )
                    finally:
                        _unlock_file(f.fileno())
                
                # Atomic rename (on same filesystem, this is atomic)
                os.replace(temp_path, path)
                return True
                
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
                
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")
            return False
    
    @staticmethod
    def load_or_init(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Load YAML file or create with default if it doesn't exist.
        
        Args:
            path: Path to YAML file
            default: Default data if file doesn't exist
            
        Returns:
            Loaded data or default
        """
        data = AtomicYAML.load(path)
        if data is None:
            AtomicYAML.save(path, default)
            return default
        return data

"""
Tests for FileOps tool
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path
from zenus_core.tools.file_ops import FileOps


class TestFileOps:
    """Test FileOps tool operations"""
    
    def setup_method(self):
        """Set up test environment"""
        self.tool = FileOps()
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_scan_directory(self):
        """Scan should list directory contents"""
        # Create test files
        Path(self.test_dir, "file1.txt").touch()
        Path(self.test_dir, "file2.txt").touch()
        os.makedirs(Path(self.test_dir, "subdir"))
        
        result = self.tool.scan(self.test_dir)
        
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir" in result
    
    def test_mkdir_creates_directory(self):
        """Mkdir should create directories"""
        new_dir = Path(self.test_dir, "newdir")
        
        result = self.tool.mkdir(str(new_dir))
        
        assert os.path.isdir(new_dir)
        assert "Directory created" in result
    
    def test_mkdir_creates_nested_directories(self):
        """Mkdir should create nested paths"""
        nested = Path(self.test_dir, "a", "b", "c")
        
        self.tool.mkdir(str(nested))
        
        assert os.path.isdir(nested)
    
    def test_mkdir_idempotent(self):
        """Mkdir should not fail if directory exists"""
        new_dir = Path(self.test_dir, "existing")
        os.makedirs(new_dir)
        
        # Should not raise
        self.tool.mkdir(str(new_dir))
    
    def test_move_file(self):
        """Move should relocate files"""
        source = Path(self.test_dir, "source.txt")
        dest_dir = Path(self.test_dir, "dest")
        os.makedirs(dest_dir)
        
        source.write_text("test content")
        
        result = self.tool.move(str(source), str(dest_dir))
        
        assert not source.exists()
        assert (dest_dir / "source.txt").exists()
        assert "Moved files" in result
    
    def test_write_file_creates_file(self):
        """Write file should create file with content"""
        file_path = Path(self.test_dir, "test.txt")
        content = "Hello, Zenus!"
        
        result = self.tool.write_file(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text() == content
        assert "File written" in result
    
    def test_write_file_creates_parent_dirs(self):
        """Write file should create parent directories"""
        file_path = Path(self.test_dir, "nested", "path", "file.txt")
        
        self.tool.write_file(str(file_path), "content")
        
        assert file_path.exists()
    
    def test_touch_creates_empty_file(self):
        """Touch should create empty files"""
        file_path = Path(self.test_dir, "empty.txt")
        
        result = self.tool.touch(str(file_path))
        
        assert file_path.exists()
        assert file_path.stat().st_size == 0
        assert "File created" in result
    
    def test_touch_creates_parent_dirs(self):
        """Touch should create parent directories"""
        file_path = Path(self.test_dir, "nested", "empty.txt")
        
        self.tool.touch(str(file_path))
        
        assert file_path.exists()

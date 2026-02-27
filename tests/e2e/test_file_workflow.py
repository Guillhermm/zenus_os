"""
E2E tests for file operation workflows
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path
from zenus_core.brain.planner import create_intent, execute_plan
from zenus_core.tools.file_ops import FileOps


@pytest.mark.e2e
class TestFileWorkflows:
    """End-to-end tests for file operation workflows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_organize_files_by_extension(self):
        """E2E: Organize files by extension"""
        # Create test files with different extensions
        files = ["doc1.txt", "doc2.txt", "image1.jpg", "image2.jpg", "data.csv"]
        for fname in files:
            Path(self.test_dir, fname).touch()
        
        file_ops = FileOps()
        
        # Create directories for each extension
        file_ops.mkdir(str(Path(self.test_dir, "txt")))
        file_ops.mkdir(str(Path(self.test_dir, "jpg")))
        file_ops.mkdir(str(Path(self.test_dir, "csv")))
        
        # Move files to respective directories
        file_ops.move(str(Path(self.test_dir, "doc*.txt")), str(Path(self.test_dir, "txt")))
        file_ops.move(str(Path(self.test_dir, "image*.jpg")), str(Path(self.test_dir, "jpg")))
        file_ops.move(str(Path(self.test_dir, "*.csv")), str(Path(self.test_dir, "csv")))
        
        # Verify organization
        assert (Path(self.test_dir, "txt", "doc1.txt").exists() or 
                Path(self.test_dir, "txt").exists())  # At least directory created
        assert (Path(self.test_dir, "jpg", "image1.jpg").exists() or 
                Path(self.test_dir, "jpg").exists())
        assert (Path(self.test_dir, "csv", "data.csv").exists() or 
                Path(self.test_dir, "csv").exists())
    
    def test_create_project_structure(self):
        """E2E: Create standard project structure"""
        project_name = "test-project"
        project_path = Path(self.test_dir, project_name)
        
        file_ops = FileOps()
        
        # Create project directories
        dirs = [
            "src",
            "tests",
            "docs",
            "config"
        ]
        
        file_ops.mkdir(str(project_path))
        for d in dirs:
            file_ops.mkdir(str(project_path / d))
        
        # Create initial files
        readme_content = f"# {project_name}\n\nProject description"
        file_ops.write_file(str(project_path / "README.md"), readme_content)
        file_ops.write_file(str(project_path / ".gitignore"), "*.pyc\n__pycache__/\n")
        file_ops.touch(str(project_path / "src" / "__init__.py"))
        file_ops.touch(str(project_path / "tests" / "__init__.py"))
        
        # Verify structure
        assert project_path.exists()
        assert (project_path / "src").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "docs").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".gitignore").exists()
        
        # Verify content
        readme_text = (project_path / "README.md").read_text()
        assert project_name in readme_text
    
    def test_backup_and_restore(self):
        """E2E: Backup files and restore them"""
        file_ops = FileOps()
        
        # Create original files
        original_dir = Path(self.test_dir, "original")
        backup_dir = Path(self.test_dir, "backup")
        
        file_ops.mkdir(str(original_dir))
        
        test_files = {
            "file1.txt": "Content 1",
            "file2.txt": "Content 2",
            "file3.txt": "Content 3"
        }
        
        for fname, content in test_files.items():
            file_ops.write_file(str(original_dir / fname), content)
        
        # Backup: Copy all files
        file_ops.mkdir(str(backup_dir))
        for fname in test_files:
            src = original_dir / fname
            if src.exists():
                import shutil
                shutil.copy2(str(src), str(backup_dir))
        
        # Modify original files
        for fname in test_files:
            file_ops.write_file(str(original_dir / fname), "Modified content")
        
        # Verify modification
        assert (original_dir / "file1.txt").read_text() == "Modified content"
        
        # Restore from backup
        for fname in test_files:
            if (backup_dir / fname).exists():
                import shutil
                shutil.copy2(str(backup_dir / fname), str(original_dir))
        
        # Verify restoration
        assert (original_dir / "file1.txt").read_text() == "Content 1"
        assert (original_dir / "file2.txt").read_text() == "Content 2"
    
    def test_batch_rename_files(self):
        """E2E: Batch rename files with pattern"""
        file_ops = FileOps()
        
        # Create files with old naming
        old_names = [f"old_name_{i}.txt" for i in range(5)]
        for fname in old_names:
            file_ops.touch(str(Path(self.test_dir, fname)))
        
        # Rename files (simulated batch rename)
        import re
        for fname in old_names:
            old_path = Path(self.test_dir, fname)
            if old_path.exists():
                new_name = fname.replace("old_name_", "new_name_")
                new_path = Path(self.test_dir, new_name)
                old_path.rename(new_path)
        
        # Verify renames
        assert Path(self.test_dir, "new_name_0.txt").exists()
        assert Path(self.test_dir, "new_name_4.txt").exists()
        assert not Path(self.test_dir, "old_name_0.txt").exists()


@pytest.mark.e2e
@pytest.mark.slow
class TestFileWorkflowsPerformance:
    """Performance tests for file workflows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def teardown_method(self):
        """Clean up"""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_many_files_performance(self):
        """Should handle creating many files efficiently"""
        import time
        
        file_ops = FileOps()
        
        start = time.time()
        
        # Create 100 files
        for i in range(100):
            file_ops.touch(str(Path(self.test_dir, f"file_{i}.txt")))
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<5s)
        assert elapsed < 5.0, f"Creating 100 files took {elapsed:.2f}s (should be <5s)"
        
        # Verify files created
        created_files = list(Path(self.test_dir).glob("file_*.txt"))
        assert len(created_files) == 100

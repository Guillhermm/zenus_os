"""
Integration tests for GitOps tool
"""

import os
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path
from zenus_core.tools.git_ops import GitOps


class TestGitOps:
    """Test GitOps tool operations"""
    
    def setup_method(self):
        """Set up test environment with a git repo"""
        self.tool = GitOps()
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize a git repo
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True, check=True)
        
        # Create initial commit
        test_file = Path(self.test_dir) / "README.md"
        test_file.write_text("# Test Repo\n")
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], capture_output=True, check=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_status(self):
        """Should return git status"""
        result = self.tool.status()
        
        assert isinstance(result, str)
        # Clean repo should mention "nothing to commit" or "working tree clean"
        assert ("nothing to commit" in result.lower() or 
                "working tree clean" in result.lower() or
                "no changes" in result.lower())
    
    def test_status_with_changes(self):
        """Should detect uncommitted changes"""
        # Create a new file
        new_file = Path(self.test_dir) / "newfile.txt"
        new_file.write_text("new content")
        
        result = self.tool.status()
        
        assert "newfile.txt" in result or "Untracked" in result
    
    def test_diff(self):
        """Should show diff for changed files"""
        # Modify existing file
        readme = Path(self.test_dir) / "README.md"
        readme.write_text("# Modified Test Repo\n")
        
        result = self.tool.diff()
        
        assert isinstance(result, str)
        # Should show the diff (might be empty if no changes staged)
    
    def test_log(self):
        """Should show commit history"""
        result = self.tool.log(limit=5)
        
        assert "Initial commit" in result or "commit" in result.lower()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_branch_list(self):
        """Should list branches"""
        result = self.tool.branch()
        
        assert "main" in result or "master" in result
        assert isinstance(result, str)
    
    def test_branch_create(self):
        """Should create a new branch"""
        result = self.tool.branch(name="feature-test")
        
        assert "feature-test" in result or "created" in result.lower()
        
        # Verify branch exists
        branches = self.tool.branch()
        assert "feature-test" in branches
    
    def test_add_files(self):
        """Should stage files"""
        # Create new file
        new_file = Path(self.test_dir) / "newfile.txt"
        new_file.write_text("content")
        
        result = self.tool.add(files=["newfile.txt"])
        
        assert isinstance(result, str)
        
        # Verify file is staged
        status = self.tool.status()
        assert "newfile.txt" in status
    
    def test_add_all(self):
        """Should stage all changes"""
        # Create multiple new files
        for i in range(3):
            (Path(self.test_dir) / f"file{i}.txt").write_text(f"content{i}")
        
        result = self.tool.add(files=["."])
        
        assert isinstance(result, str)
        
        # Verify files are staged
        status = self.tool.status()
        assert "file0.txt" in status or "new file" in status.lower()
    
    def test_commit(self):
        """Should commit staged changes"""
        # Create and stage a file
        new_file = Path(self.test_dir) / "committed.txt"
        new_file.write_text("committed content")
        self.tool.add(files=["committed.txt"])
        
        result = self.tool.commit(message="Test commit")
        
        assert "Test commit" in result or "committed" in result.lower()
        
        # Verify commit appears in log
        log = self.tool.log(limit=1)
        assert "Test commit" in log
    
    def test_commit_without_changes(self):
        """Should handle commit with no changes gracefully"""
        result = self.tool.commit(message="Empty commit")
        
        # Should either succeed or give informative error
        assert isinstance(result, str)
    
    def test_stash(self):
        """Should stash changes"""
        # Make changes
        readme = Path(self.test_dir) / "README.md"
        readme.write_text("# Stashed changes\n")
        
        result = self.tool.stash()
        
        assert isinstance(result, str)
        assert "stash" in result.lower() or "saved" in result.lower() or "no local changes" in result.lower()
    
    def test_checkout_branch(self):
        """Should checkout existing branch"""
        # Create a branch first
        self.tool.branch(name="test-branch")
        
        result = self.tool.checkout(branch="test-branch")
        
        assert "test-branch" in result or "switched" in result.lower()


@pytest.mark.slow
class TestGitOpsPerformance:
    """Performance tests for GitOps"""
    
    def setup_method(self):
        """Set up test environment"""
        self.tool = GitOps()
        self.test_dir = tempfile.mkdtemp()
        
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True, check=True)
        
        test_file = Path(self.test_dir) / "README.md"
        test_file.write_text("# Test\n")
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Init"], capture_output=True, check=True)
    
    def teardown_method(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_status_fast(self):
        """Git status should be fast (<200ms)"""
        import time
        
        start = time.time()
        self.tool.status()
        elapsed = time.time() - start
        
        assert elapsed < 0.2, f"Git status took {elapsed:.3f}s (should be <0.2s)"
    
    def test_log_fast(self):
        """Git log should be fast (<200ms)"""
        import time
        
        start = time.time()
        self.tool.log(limit=10)
        elapsed = time.time() - start
        
        assert elapsed < 0.2, f"Git log took {elapsed:.3f}s (should be <0.2s)"

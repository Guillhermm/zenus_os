"""
Enhanced TextOps Tests

Test real-world scenarios users report as difficult.
"""

import pytest
import os
import tempfile
from zenus_core.tools.text_ops import TextOps


@pytest.fixture
def text_ops():
    return TextOps()


@pytest.fixture
def temp_file():
    """Create a temp file for testing"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_write_new_file(text_ops, temp_file):
    """Test writing to a new file"""
    os.unlink(temp_file)  # Remove it first
    
    result = text_ops.write(temp_file, "Hello World")
    
    assert "Wrote" in result
    assert os.path.exists(temp_file)
    with open(temp_file) as f:
        assert f.read() == "Hello World"


def test_write_overwrite_existing(text_ops, temp_file):
    """Test overwriting an existing file"""
    # Write initial content
    with open(temp_file, 'w') as f:
        f.write("Original")
    
    # Overwrite
    result = text_ops.write(temp_file, "New Content")
    
    assert "Overwrote" in result or "Wrote" in result
    with open(temp_file) as f:
        assert f.read() == "New Content"


def test_write_multiline(text_ops, temp_file):
    """Test writing multiline content"""
    content = "Line 1\nLine 2\nLine 3"
    
    text_ops.write(temp_file, content)
    
    with open(temp_file) as f:
        assert f.read() == content


def test_read_small_file(text_ops, temp_file):
    """Test reading a small file"""
    content = "Test content\nSecond line"
    with open(temp_file, 'w') as f:
        f.write(content)
    
    result = text_ops.read(temp_file)
    
    assert content in result
    assert "File content" in result


def test_read_large_file(text_ops, temp_file):
    """Test reading gets truncated for large files"""
    # Write 20,000 chars
    content = "x" * 20000
    with open(temp_file, 'w') as f:
        f.write(content)
    
    result = text_ops.read(temp_file)
    
    assert "truncated" in result
    assert len(result) < len(content)


def test_append_to_existing(text_ops, temp_file):
    """Test appending to existing file"""
    with open(temp_file, 'w') as f:
        f.write("First line\n")
    
    text_ops.append(temp_file, "Second line\n")
    
    with open(temp_file) as f:
        content = f.read()
        assert "First line" in content
        assert "Second line" in content


def test_search_case_insensitive(text_ops, temp_file):
    """Test case-insensitive search"""
    with open(temp_file, 'w') as f:
        f.write("Hello World\nHELLO again\nhello there")
    
    result = text_ops.search(temp_file, "hello", case_sensitive=False)
    
    assert "3 matches" in result


def test_search_case_sensitive(text_ops, temp_file):
    """Test case-sensitive search"""
    with open(temp_file, 'w') as f:
        f.write("Hello World\nHELLO again\nhello there")
    
    result = text_ops.search(temp_file, "hello", case_sensitive=True)
    
    assert "1 matches" in result or "1 match" in result.lower()


def test_count_lines(text_ops, temp_file):
    """Test line counting"""
    with open(temp_file, 'w') as f:
        f.write("Line 1\nLine 2\nLine 3\n")
    
    result = text_ops.count_lines(temp_file)
    
    assert "3 lines" in result


def test_head_default(text_ops, temp_file):
    """Test head with default 10 lines"""
    with open(temp_file, 'w') as f:
        for i in range(20):
            f.write(f"Line {i}\n")
    
    result = text_ops.head(temp_file)
    
    assert "Line 0" in result
    assert "Line 9" in result
    assert "Line 10" not in result


def test_tail_default(text_ops, temp_file):
    """Test tail with default 10 lines"""
    with open(temp_file, 'w') as f:
        for i in range(20):
            f.write(f"Line {i}\n")
    
    result = text_ops.tail(temp_file)
    
    assert "Line 19" in result
    assert "Line 10" in result
    assert "Line 9" not in result


def test_write_creates_parent_directories(text_ops):
    """Test that write creates parent directories"""
    temp_dir = tempfile.mkdtemp()
    nested_file = os.path.join(temp_dir, "sub", "dir", "file.txt")
    
    try:
        text_ops.write(nested_file, "Content")
        
        assert os.path.exists(nested_file)
        with open(nested_file) as f:
            assert f.read() == "Content"
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_read_nonexistent_file(text_ops):
    """Test reading nonexistent file raises error"""
    with pytest.raises(FileNotFoundError):
        text_ops.read("/nonexistent/file.txt")


def test_write_empty_content(text_ops, temp_file):
    """Test writing empty content"""
    result = text_ops.write(temp_file, "")
    
    assert os.path.exists(temp_file)
    with open(temp_file) as f:
        assert f.read() == ""


def test_write_unicode(text_ops, temp_file):
    """Test writing Unicode content"""
    content = "Hello 世界 🌍 Привет"
    
    text_ops.write(temp_file, content)
    
    with open(temp_file, encoding='utf-8') as f:
        assert f.read() == content

#!/usr/bin/env python3
"""
Test script to verify storage module functionality
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.append('backend')

try:
    from report_service.storage import FileStorage, file_storage
    print("✅ Storage module imported successfully!")
    print()
    
    # Test 1: Basic FileStorage instantiation
    print("🧪 Test 1: FileStorage instantiation")
    test_storage = FileStorage("test_storage")
    print(f"✅ Created FileStorage with base path: {test_storage.base_path}")
    print(f"✅ Base path exists: {test_storage.base_path.exists()}")
    print()
    
    # Test 2: File save and retrieve
    print("🧪 Test 2: File save and retrieve")
    test_content = b"Hello, this is a test file content!"
    test_filename = "test_file.txt"
    
    # Save file
    saved_path = test_storage.save_file(test_content, test_filename, "test_subdir")
    print(f"✅ File saved to: {saved_path}")
    
    # Get file path
    retrieved_path = test_storage.get_file_path(test_filename, "test_subdir")
    print(f"✅ Retrieved file path: {retrieved_path}")
    
    # Verify file content
    with open(saved_path, 'rb') as f:
        content = f.read()
    print(f"✅ File content matches: {content == test_content}")
    print()
    
    # Test 3: List files
    print("🧪 Test 3: List files")
    files = test_storage.list_files("test_subdir")
    print(f"✅ Files in test_subdir: {files}")
    print(f"✅ Test file found: {test_filename in files}")
    print()
    
    # Test 4: Create temp file
    print("🧪 Test 4: Create temp file")
    temp_path = test_storage.create_temp_file(suffix=".tmp", prefix="test_")
    print(f"✅ Temp file created: {temp_path}")
    print(f"✅ Temp file exists: {Path(temp_path).exists()}")
    print()
    
    # Test 5: Delete file
    print("🧪 Test 5: Delete file")
    delete_result = test_storage.delete_file(test_filename, "test_subdir")
    print(f"✅ File deletion successful: {delete_result}")
    
    # Verify deletion
    files_after_delete = test_storage.list_files("test_subdir")
    print(f"✅ Files after deletion: {files_after_delete}")
    print(f"✅ File no longer exists: {test_filename not in files_after_delete}")
    print()
    
    # Test 6: Global file_storage instance
    print("🧪 Test 6: Global file_storage instance")
    print(f"✅ Global instance type: {type(file_storage)}")
    print(f"✅ Global instance base path: {file_storage.base_path}")
    print()
    
    # Test 7: Error handling
    print("🧪 Test 7: Error handling")
    # Try to get non-existent file
    non_existent = test_storage.get_file_path("non_existent.txt")
    print(f"✅ Non-existent file returns None: {non_existent is None}")
    
    # Try to delete non-existent file
    delete_non_existent = test_storage.delete_file("non_existent.txt")
    print(f"✅ Delete non-existent file returns False: {delete_non_existent is False}")
    print()
    
    # Test 8: Multiple subdirectories
    print("🧪 Test 8: Multiple subdirectories")
    test_storage.save_file(b"subdir1 content", "file1.txt", "subdir1")
    test_storage.save_file(b"subdir2 content", "file2.txt", "subdir2")
    
    subdir1_files = test_storage.list_files("subdir1")
    subdir2_files = test_storage.list_files("subdir2")
    print(f"✅ Subdir1 files: {subdir1_files}")
    print(f"✅ Subdir2 files: {subdir2_files}")
    print()
    
    # Cleanup
    print("🧹 Cleanup")
    try:
        shutil.rmtree("test_storage")
        print("✅ Test storage directory cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    # Clean up temp file
    try:
        os.unlink(temp_path)
        print("✅ Temp file cleaned up")
    except Exception as e:
        print(f"⚠️ Temp file cleanup warning: {e}")
    
    print()
    print("🎉 All storage tests completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This might indicate missing dependencies or incorrect module structure")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc() 
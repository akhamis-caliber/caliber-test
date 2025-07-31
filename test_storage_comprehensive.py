#!/usr/bin/env python3
"""
Comprehensive storage module test
Tests all storage functionality including edge cases
"""

import sys
import os
import tempfile
import shutil
import time
from pathlib import Path

# Add backend to path
sys.path.append('backend')

def test_storage_basic_operations():
    """Test basic storage operations"""
    print("🧪 Testing Basic Storage Operations")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage
        
        # Create test storage
        test_storage = FileStorage("test_storage_comprehensive")
        
        # Test 1: Save and retrieve file
        test_content = "This is a test file content with special characters: éñüß".encode('utf-8')
        filename = "test_file.txt"
        
        saved_path = test_storage.save_file(test_content, filename, "test_dir")
        print(f"✅ File saved to: {saved_path}")
        
        # Verify file exists
        retrieved_path = test_storage.get_file_path(filename, "test_dir")
        assert retrieved_path == saved_path, "File path mismatch"
        print("✅ File path retrieval works")
        
        # Verify content
        with open(saved_path, 'rb') as f:
            content = f.read()
        assert content == test_content, "File content mismatch"
        print("✅ File content verification works")
        
        # Test 2: List files
        files = test_storage.list_files("test_dir")
        assert filename in files, "File not found in listing"
        print(f"✅ File listing works: {files}")
        
        # Test 3: Delete file
        delete_result = test_storage.delete_file(filename, "test_dir")
        assert delete_result == True, "File deletion failed"
        print("✅ File deletion works")
        
        # Verify deletion
        files_after_delete = test_storage.list_files("test_dir")
        assert filename not in files_after_delete, "File still exists after deletion"
        print("✅ File deletion verification works")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False

def test_storage_temp_files():
    """Test temporary file operations"""
    print("\n🧪 Testing Temporary File Operations")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage
        
        test_storage = FileStorage("test_storage_comprehensive")
        
        # Test temp file creation
        temp_path1 = test_storage.create_temp_file(suffix=".tmp", prefix="test_")
        temp_path2 = test_storage.create_temp_file(suffix=".log", prefix="test_")
        
        print(f"✅ Temp file 1 created: {temp_path1}")
        print(f"✅ Temp file 2 created: {temp_path2}")
        
        # Verify files exist
        assert Path(temp_path1).exists(), "Temp file 1 doesn't exist"
        assert Path(temp_path2).exists(), "Temp file 2 doesn't exist"
        print("✅ Temp files exist")
        
        # Test writing to temp files
        content1 = b"Temp file 1 content"
        content2 = b"Temp file 2 content"
        
        with open(temp_path1, 'wb') as f:
            f.write(content1)
        with open(temp_path2, 'wb') as f:
            f.write(content2)
        
        print("✅ Temp file writing works")
        
        # Test reading from temp files
        with open(temp_path1, 'rb') as f:
            read_content1 = f.read()
        with open(temp_path2, 'rb') as f:
            read_content2 = f.read()
        
        assert read_content1 == content1, "Temp file 1 content mismatch"
        assert read_content2 == content2, "Temp file 2 content mismatch"
        print("✅ Temp file reading works")
        
        return True
        
    except Exception as e:
        print(f"❌ Temp file operations failed: {e}")
        return False

def test_storage_subdirectories():
    """Test subdirectory operations"""
    print("\n🧪 Testing Subdirectory Operations")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage
        
        test_storage = FileStorage("test_storage_comprehensive")
        
        # Create multiple subdirectories
        subdirs = ["dir1", "dir2", "dir3", "nested/dir4"]
        
        for subdir in subdirs:
            content = f"Content for {subdir}".encode()
            filename = f"file_{subdir.replace('/', '_')}.txt"
            test_storage.save_file(content, filename, subdir)
            print(f"✅ Created file in {subdir}: {filename}")
        
        # Test listing files in each subdirectory
        for subdir in subdirs:
            files = test_storage.list_files(subdir)
            expected_file = f"file_{subdir.replace('/', '_')}.txt"
            assert expected_file in files, f"Expected file not found in {subdir}"
            print(f"✅ Files in {subdir}: {files}")
        
        # Test nested directory structure
        nested_files = test_storage.list_files("nested")
        assert "file_nested_dir4.txt" in nested_files, "Nested file not found"
        print("✅ Nested directory structure works")
        
        return True
        
    except Exception as e:
        print(f"❌ Subdirectory operations failed: {e}")
        return False

def test_storage_error_handling():
    """Test error handling"""
    print("\n🧪 Testing Error Handling")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage
        
        test_storage = FileStorage("test_storage_comprehensive")
        
        # Test 1: Get non-existent file
        non_existent = test_storage.get_file_path("non_existent.txt")
        assert non_existent is None, "Should return None for non-existent file"
        print("✅ Non-existent file handling works")
        
        # Test 2: Delete non-existent file
        delete_result = test_storage.delete_file("non_existent.txt")
        assert delete_result == False, "Should return False for non-existent file deletion"
        print("✅ Non-existent file deletion handling works")
        
        # Test 3: List files in non-existent directory
        empty_list = test_storage.list_files("non_existent_dir")
        assert empty_list == [], "Should return empty list for non-existent directory"
        print("✅ Non-existent directory listing works")
        
        # Test 4: Read non-existent file (should raise FileNotFoundError)
        try:
            test_storage.read_file("non_existent_file.txt")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            print("✅ FileNotFoundError raised correctly for non-existent file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
        return False

def test_storage_cleanup():
    """Test cleanup functionality"""
    print("\n🧪 Testing Cleanup Functionality")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage
        
        test_storage = FileStorage("test_storage_comprehensive")
        
        # Create some temp files
        temp_files = []
        for i in range(3):
            temp_path = test_storage.create_temp_file(suffix=f"_{i}.tmp", prefix="cleanup_test_")
            temp_files.append(temp_path)
            
            # Write some content
            with open(temp_path, 'wb') as f:
                f.write(f"Temp file {i} content".encode())
        
        print(f"✅ Created {len(temp_files)} temp files for cleanup test")
        
        # Test cleanup function
        test_storage.cleanup_temp_files(max_age_hours=0)  # Clean up immediately
        
        # Verify files are cleaned up
        for temp_file in temp_files:
            assert not Path(temp_file).exists(), f"Temp file {temp_file} still exists after cleanup"
        
        print("✅ Cleanup functionality works")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup functionality failed: {e}")
        return False

def test_global_storage_instance():
    """Test global storage instance"""
    print("\n🧪 Testing Global Storage Instance")
    print("=" * 50)
    
    try:
        from report_service.storage import file_storage
        
        # Test global instance
        assert file_storage is not None, "Global storage instance is None"
        print(f"✅ Global storage instance: {type(file_storage)}")
        print(f"✅ Global storage base path: {file_storage.base_path}")
        
        # Test basic operation with global instance
        test_content = b"Global instance test content"
        filename = "global_test.txt"
        
        saved_path = file_storage.save_file(test_content, filename, "global_test")
        print(f"✅ Global instance save: {saved_path}")
        
        # Verify
        retrieved_path = file_storage.get_file_path(filename, "global_test")
        assert retrieved_path == saved_path, "Global instance path mismatch"
        
        with open(saved_path, 'rb') as f:
            content = f.read()
        assert content == test_content, "Global instance content mismatch"
        
        # Cleanup
        file_storage.delete_file(filename, "global_test")
        print("✅ Global instance operations work")
        
        return True
        
    except Exception as e:
        print(f"❌ Global storage instance failed: {e}")
        return False

def main():
    """Run all storage tests"""
    print("🚀 CALIBER-01 Comprehensive Storage Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Basic Operations", test_storage_basic_operations),
        ("Temp Files", test_storage_temp_files),
        ("Subdirectories", test_storage_subdirectories),
        ("Error Handling", test_storage_error_handling),
        ("Cleanup", test_storage_cleanup),
        ("Global Instance", test_global_storage_instance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        results[test_name] = test_func()
        print()
    
    # Summary
    print("📊 Storage Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} storage tests passed")
    
    # Cleanup test directory
    try:
        shutil.rmtree("test_storage_comprehensive")
        print("✅ Test storage directory cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    if passed == total:
        print("🎉 All storage functionality is working correctly!")
    else:
        print("⚠️ Some storage functionality needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
import os

def check_file_for_null_bytes(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if b'\x00' in content:
                return True
        return False
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return False

def find_files_with_null_bytes(directory):
    files_with_null_bytes = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if check_file_for_null_bytes(file_path):
                    files_with_null_bytes.append(file_path)
    
    return files_with_null_bytes

if __name__ == "__main__":
    directory = "."  # Current directory
    files = find_files_with_null_bytes(directory)
    
    if files:
        print("Files containing null bytes:")
        for file in files:
            print(f"- {file}")
    else:
        print("No files with null bytes found.") 
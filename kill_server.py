import os
import sys
import subprocess

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    try:
        if sys.platform == 'win32':
            # Windows
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )
            
            if result.stdout:
                # Extract PID(s)
                for line in result.stdout.strip().split('\n'):
                    if f':{port}' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            print(f"Found process with PID {pid} on port {port}")
                            try:
                                subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
                                print(f"Successfully killed process with PID {pid}")
                            except subprocess.CalledProcessError:
                                print(f"Failed to kill process with PID {pid}")
            else:
                print(f"No process found running on port {port}")
                
        else:
            # Unix/Linux/Mac
            result = subprocess.run(
                f"lsof -i :{port} | grep LISTEN | awk '{{print $2}}'",
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )
            
            if result.stdout:
                pid = result.stdout.strip()
                print(f"Found process with PID {pid} on port {port}")
                subprocess.run(f'kill -9 {pid}', shell=True, check=True)
                print(f"Successfully killed process with PID {pid}")
            else:
                print(f"No process found running on port {port}")
                
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        
if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
            
    kill_process_on_port(port) 
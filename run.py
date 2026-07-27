import os
import sys
import subprocess

def get_venv_python():
    if os.name == 'nt':
        return os.path.join('.venv', 'Scripts', 'python.exe')
    return os.path.join('.venv', 'bin', 'python')

def is_venv():
    return sys.prefix != sys.base_prefix or 'VIRTUAL_ENV' in os.environ

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    if not is_venv():
        print("Bootstrapping virtual environment...")
        if not os.path.exists('.venv'):
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print("Virtual environment created.")
        
        # Run this script again using the venv python
        venv_python = get_venv_python()
        if not os.path.exists(venv_python):
            print(f"Error: Virtual environment python not found at {venv_python}")
            sys.exit(1)
            
        print("Re-launching application inside virtual environment...")
        # Forward args
        result = subprocess.run([venv_python, __file__] + sys.argv[1:])
        sys.exit(result.returncode)

    else:
        print("Running inside virtual environment.")
        print("Updating dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("Starting FastAPI AI Attendance Server...")
        # Import uvicorn inside venv to run
        import uvicorn
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()

import os
import platform
import subprocess
import shutil
import glob
import sys

def check_environment():
    """Check if running in Anaconda and provide appropriate guidance"""
    in_conda = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
    if in_conda:
        print("\nAnaconda environment detected!")
        print("To build this application, please:")
        print("1. Create a clean virtual environment:")
        print("   python -m venv venv")
        print("2. Activate the environment:")
        print("   Windows: .\\venv\\Scripts\\activate")
        print("   Linux/Mac: source venv/bin/activate")
        print("3. Install requirements:")
        print("   pip install -r requirements.txt")
        print("4. Run this script again in the virtual environment")
        return False
    return True

def clean_build():
    """Clean up build artifacts"""
    print("Cleaning previous builds...")
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name} directory")
    
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            os.remove(file)
            print(f"Removed {file}")

def build_application():
    """Build the application for the current platform"""
    system = platform.system().lower()
    print(f"\nBuilding for {system}...")
    
    # Check for required files
    required_files = ['LICENSE', 'README.md']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Warning: {file} not found, continuing without it...")
            required_files.remove(file)
    
    # Base PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=FolderSyncer',
        '--windowed',  # Use --noconsole on Windows
        '--onefile',   # Create a single executable
        '--clean',     # Clean PyInstaller cache
    ]
    
    # Add data files
    for file in required_files:
        cmd.extend(['--add-data', f'{file}{os.pathsep}.'])
    
    # Add main script
    cmd.append('src/main.py')
    
    # Platform-specific options
    if system == 'windows':
        cmd.append('--noconsole')  # Windows-specific no console
        if os.path.exists('resources/icon.ico'):
            cmd.extend(['--icon', 'resources/icon.ico'])
    elif system == 'darwin':
        if os.path.exists('resources/icon.icns'):
            cmd.extend(['--icon', 'resources/icon.icns'])
        cmd.extend(['--osx-bundle-identifier', 'com.foldersyncer'])
    
    print("\nExecuting PyInstaller with command:")
    print(' '.join(cmd))
    
    try:
        # Execute PyInstaller
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\nError during build process: {e}")
        print("\nFor detailed error information, check the build output above.")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False
    
    return True

def main():
    print("Starting build process...")
    
    # Check environment
    if not check_environment():
        return
    
    try:
        # Ensure required packages are installed
        print("\nInstalling required packages...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', 'watchdog'], check=True)
        
        # Clean previous builds
        clean_build()
        
        # Build the application
        if build_application():
            print("\nBuild successful! Executable can be found in the 'dist' directory.")
            # Show the exact path to the executable
            if os.path.exists('dist'):
                files = os.listdir('dist')
                if files:
                    print("Created files:")
                    for file in files:
                        print(f"- {os.path.abspath(os.path.join('dist', file))}")
        else:
            print("\nBuild process failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\nError during build process: {e}")
        print("Please ensure you're running this script in a clean Python environment.")

if __name__ == "__main__":
    main()

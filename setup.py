# setup.py - Installation and fix script
import subprocess
import sys
import os

def install_requirements():
    """Install requirements with compatible versions"""
    print("Installing requirements...")
    
    # First uninstall problematic packages
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", 
                          "numpy", "pandas", "numexpr", "bottleneck"])
    
    # Install compatible numpy first
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==1.26.4"])
    
    # Install other requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("Installation complete!")

def check_imports():
    """Check that all imports work"""
    try:
        import numpy
        print(f"✓ NumPy version: {numpy.__version__}")
        
        import pandas
        print(f"✓ Pandas version: {pandas.__version__}")
        
        import sklearn
        print(f"✓ Scikit-learn version: {sklearn.__version__}")
        
        import streamlit
        print(f"✓ Streamlit version: {streamlit.__version__}")
        
        print("\nAll imports successful!")
        return True
    except Exception as e:
        print(f"✗ Import error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up Vehicle Condition Monitoring System...")
    print("=" * 50)
    
    # Install requirements
    install_requirements()
    
    # Check imports
    print("\nChecking imports...")
    check_imports()
    
    print("\nSetup complete! You can now run: python main.py")
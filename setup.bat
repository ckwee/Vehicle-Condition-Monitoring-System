@echo off
echo ===========================================
echo Vehicle Condition Monitoring - Setup & Run
echo ===========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo Step 2: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 3: Installing compatible NumPy...
pip uninstall -y numpy pandas numexpr bottleneck
pip install numpy==1.26.4

echo.
echo Step 4: Installing requirements...
pip install -r requirements.txt

echo.
echo Step 5: Creating necessary directories...
if not exist "agents" mkdir agents
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo Step 6: Creating __init__.py files...
echo # Agents package > agents\__init__.py

echo.
echo ===========================================
echo Setup complete! Running the system...
echo ===========================================
echo.

python main.py

pause
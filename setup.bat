@echo off
echo Setting up Pose Estimation Application...

:: Upgrade pip
python -m pip install --upgrade pip

:: Install dependencies
pip install -r requirements.txt

:: Install the application
python setup.py install

echo Setup complete!
pause 
py -3.10 -m PyInstaller --log-level=WARN randomizer.spec
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.10 build.py
if %errorlevel% neq 0 exit /b %errorlevel%
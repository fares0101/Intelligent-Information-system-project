@echo off
echo Initializing Git repository for Smart Maze Game...

git init
git add .
git commit -m "Initial commit: Smart Maze Game"

echo.
echo Repository initialized successfully!
echo.
echo Next steps:
echo 1. Create a repository on GitHub
echo 2. Run the following commands:
echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo Press any key to exit...
pause > nul 
@echo off
echo ============================================
echo Credit Card Fraud Detection - Push to GitHub
echo ============================================
echo.
echo This script will push your code to GitHub.
echo.
echo Prerequisites:
echo 1. Git must be installed
echo 2. You must have GitHub credentials configured
echo    (Use: git config --global user.name "Your Name")
echo    (Use: git config --global user.email "your.email@example.com")
echo.
echo Or use GitHub CLI: gh auth login
echo.
pause
echo.
echo Pushing to GitHub...
echo.
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo SUCCESS! Code pushed to GitHub.
    echo.
    echo Repository URL: https://github.com/Navid-A-08/Credit-Card-Fraud-Detection
    echo ============================================
) else (
    echo ============================================
    echo ERROR: Push failed.
    echo.
    echo Please ensure you have:
    echo 1. GitHub credentials configured
    echo 2. Access to the repository
    echo.
    echo Try running: gh auth login
    echo Or: git config --global credential.helper store
    echo ============================================
)
pause

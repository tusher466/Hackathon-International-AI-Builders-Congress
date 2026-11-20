@echo off
echo Creating desktop shortcut for Factory Brain...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Factory Brain.lnk'); $Shortcut.TargetPath = '%~dp0Run Factory Brain.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'shell32.dll,14'; $Shortcut.Description = 'Factory Brain Full Stack Launcher'; $Shortcut.Save(); Write-Host 'Shortcut created on Desktop: Factory Brain.lnk' -ForegroundColor Green"
echo.
echo Desktop shortcut created!
echo You can now double-click "Factory Brain" on your desktop to run the project.
pause

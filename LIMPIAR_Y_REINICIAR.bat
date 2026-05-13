@echo off
echo ========================================================
echo Limpiando tu cache de VSCode y cerrando servidores viejos...
echo ========================================================
taskkill /F /IM python.exe >nul 2>&1
echo Listo. Los servidores travados fueron eliminados.
echo.
echo ========================================================
echo Iniciando U-Ride con TODOS LOS CAMBIOS NUEVOS (Rojo)...
echo ========================================================
python run.py
pause

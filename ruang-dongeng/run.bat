@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 atau lebih baru perlu dipasang sebelum menjalankan aplikasi.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo Membuat lingkungan Python...
  %PY% -3 -m venv .venv
  if errorlevel 1 %PY% -m venv .venv
)
echo Memasang kebutuhan aplikasi...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Gagal memasang paket. Pastikan Python dan internet tersedia.
  pause
  exit /b 1
)
echo Membuka Ruang Dongeng di http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
pause

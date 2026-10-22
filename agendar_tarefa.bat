@echo off
setlocal
REM Cria a tarefa agendada usando a pasta onde este .bat esta e o python do PATH.
set "PROJETO=%~dp0"
if "%PROJETO:~-1%"=="\" set "PROJETO=%PROJETO:~0,-1%"

for /f "delims=" %%p in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%p"
if not defined PYTHON_EXE (
    echo Python nao encontrado no PATH. Instale o Python ou edite este arquivo com o caminho completo.
    pause
    exit /b 1
)

echo Criando tarefa agendada: SAC_Usuarios_Inativos (toda sexta as 10h)
echo   Python : %PYTHON_EXE%
echo   Projeto: %PROJETO%

schtasks /create /tn "SAC_Usuarios_Inativos" /tr "\"%PYTHON_EXE%\" \"%PROJETO%\main.py\"" /sc weekly /d FRI /st 10:00 /f

if %errorlevel% equ 0 (
    echo Tarefa criada com sucesso!
) else (
    echo Erro ao criar tarefa. Execute como administrador.
)
pause

@echo off
echo Criando tarefa agendada: SAC_Usuarios_Inativos (toda sexta as 10h)

schtasks /create /tn "SAC_Usuarios_Inativos" /tr "C:\Users\luan.arantes\AppData\Local\Programs\Python\Python312\python.exe \"C:\Users\luan.arantes\Desktop\Desativar usuarios SAC\main.py\"" /sc weekly /d FRI /st 10:00 /f

if %errorlevel% equ 0 (
    echo Tarefa criada com sucesso!
) else (
    echo Erro ao criar tarefa. Execute como administrador.
)
pause

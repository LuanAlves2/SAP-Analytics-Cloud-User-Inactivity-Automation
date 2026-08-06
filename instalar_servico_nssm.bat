@echo off
echo === Instalando servico SAC_Usuarios_Inativos via NSSM ===

nssm install SAC_Usuarios_Inativos "C:\Program Files\Python\python.exe" "\"C:\sistemas\SAP-Analytics-Cloud-User-Inactivity-Automation\service.py\""
nssm set SAC_Usuarios_Inativos AppDirectory "C:\sistemas\SAP-Analytics-Cloud-User-Inactivity-Automation"
nssm set SAC_Usuarios_Inativos DisplayName "SAC - Desativacao de Usuarios Inativos"
nssm set SAC_Usuarios_Inativos Description "Executa toda sexta-feira as 10h a verificacao e desativacao de usuarios inativos no SAP Analytics Cloud"
nssm set SAC_Usuarios_Inativos Start SERVICE_AUTO_START
nssm set SAC_Usuarios_Inativos AppStdout "C:\sistemas\SAP-Analytics-Cloud-User-Inactivity-Automation\service.log"
nssm set SAC_Usuarios_Inativos AppStderr "C:\sistemas\SAP-Analytics-Cloud-User-Inactivity-Automation\service.log"
nssm set SAC_Usuarios_Inativos AppStdoutCreationDisposition 4
nssm set SAC_Usuarios_Inativos AppStderrCreationDisposition 4
nssm set SAC_Usuarios_Inativos AppRotateFiles 1
nssm set SAC_Usuarios_Inativos AppRotateBytes 5242880

nssm start SAC_Usuarios_Inativos

echo.
echo Servico instalado e iniciado!
echo Logs em: C:\sistemas\SAP-Analytics-Cloud-User-Inactivity-Automation\service.log
echo.
echo Comandos uteis:
echo   nssm status SAC_Usuarios_Inativos    - ver status
echo   nssm restart SAC_Usuarios_Inativos   - reiniciar
echo   nssm stop SAC_Usuarios_Inativos      - parar
echo   nssm remove SAC_Usuarios_Inativos    - remover servico
pause

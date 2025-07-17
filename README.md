# 🛡️ SAC User Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Version](https://img.shields.io/badge/Version-1.0-orange)

</div>

Automação para análise, geração de relatórios e desativação de usuários inativos no **SAP Analytics Cloud (SAC)**. Utiliza logs de atividade, integração via API SCIM e exportação profissional para Excel.

## 🗂️ Estrutura
- `src/` – scripts Python principais
- `final/` – relatórios gerados
- `testes/` – scripts de teste
- `.env` – variáveis de ambiente (Client ID/Secret)
- `requirements.txt` – dependências do projeto

## 🚀 Instalação
1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/sac-user-automation.git
cd sac-user-automation
```
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Crie o arquivo `.env` na raiz do projeto contendo:
```bash
CLIENT_ID=seu_client_id
CLIENT_SECRET=seu_client_secret
```

## 💻 Uso
1. Exporte os relatórios de Usuários e Atividades do SAC para sua pasta `Downloads`.
2. Execute o script principal:
```bash
python src/automacao_final.py
```

O sistema irá:
- localizar automaticamente os arquivos mais recentes de usuários e atividades;
- identificar usuários inativos (mais de 40 dias sem acesso);
- gerar `usuarios_inativos_para_desativar.csv` e `.xlsx`;
- opcionalmente, desativar usuários via API SCIM.

## ✨ Funcionalidades
- **Identificação de usuários inativos** ;
- **Exportação profissional** para planilhas Excel;
- **Desativação automática** via API (com modo seguro);
- **Proteção de usuários** por lista customizável;
- **Módulos utilitários** para busca de arquivos, exportação e integrações.

## 📦 Requisitos
- Python 3.9 ou superior
- `pandas`, `requests`, `openpyxl`, `python-dotenv`

## ⚙️ Configuração
Nunca compartilhe seu `.env` publicamente. O arquivo já está no `.gitignore`.

## 💡 Aviso
Use por sua conta e risco. Revise os relatórios antes de efetuar desativações em massa.

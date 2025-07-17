with open("/mnt/data/README.md", "w", encoding="utf-8") as f:
    f.write("""
# 🛡️ SAC User Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Version](https://img.shields.io/badge/Version-1.0-orange)

</div>

## 📋 Descrição

Automação para análise, geração de relatório e desativação segura de usuários inativos no **SAP Analytics Cloud (SAC)**, utilizando logs de atividade, integração via API SCIM e exportação profissional para Excel. O sistema identifica usuários inativos, gera listas customizadas, exporta para `.xlsx` e pode desativar usuários automaticamente via API, garantindo compliance e gestão eficiente de acessos.

---

## 🗂️ Estrutura de Diretórios

📦 sac-user-automation
┣ 📂 src/ # Scripts Python principais
┣ 📂 final/ # Arquivos finais de relatórios e exportação
┣ 📂 testes/ # Scripts de teste/unitários
┣ 📜 .env # Variáveis de ambiente (Client ID/Secret)
┣ 📜 requirements.txt # Dependências do projeto
┣ 📜 README.md # Este documento



---

## 🚀 Instalação

1. Clone o repositório:

git clone https://github.com/seu-usuario/sac-user-automation.git
cd sac-user-automation
Instale as dependências:

pip install -r requirements.txt
Configure as variáveis de ambiente:
Crie um arquivo .env na raiz do projeto com seu CLIENT_ID e CLIENT_SECRET:

CLIENT_ID=seu_client_id
CLIENT_SECRET=seu_client_secret
💻 Uso
Copie os arquivos de relatório para sua pasta de Downloads:

Exporte os relatórios de Usuários e Atividades do SAC (os nomes podem ser, por exemplo, user.csv, user (2).csv, atividade.csv, etc).

Execute o script principal:

python src/automacao_final.py
O sistema irá:

Localizar automaticamente os arquivos mais recentes de usuários e atividades.

Identificar e exportar os usuários inativos (há mais de 40 dias sem atividade) para usuarios_inativos_para_desativar.csv e .xlsx.

Gerar um relatório com:

USUÁRIO (login SAC)

NOME COMPLETO

EMAIL

DIAS SEM ACESSO

LICENÇA

EMPRESA (mapeada pelo domínio do email)

Opcionalmente, desativar os usuários via API SCIM (configurável).

✨ Funcionalidades
🔎 Identificação de Usuários Inativos

Analisa automaticamente os arquivos mais recentes de usuários/atividades.

Filtra e exclui usuários protegidos (administração/configurável).

Calcula dias exatos sem acesso baseado na última atividade.

📦 Exportação Profissional

Gera relatórios .xlsx com colunas customizadas e dados de compliance para auditoria.

⚡ Desativação Automática

Realiza desativação segura de usuários inativos diretamente via API SCIM do SAC.

Busca usuários pelo email para garantir o id correto do SCIM.

Suporta modo seguro: só desativa o primeiro usuário (para testes) ou todos, conforme configuração.

🛡️ Proteção de Usuários

Lista customizável de usuários protegidos nunca serão desativados por engano.

🛠️ Principais Módulos
src/automacao_final.py: Orquestra todo o fluxo – leitura de arquivos, análise, exportação, integração SCIM e desativação.

Funções utilitárias: Modularização profissional para busca dos arquivos, cálculo de dias sem acesso, exportação, chamadas à API e proteção dos dados.

Relatórios: Exportação padronizada para Excel (.xlsx), pronto para auditoria, compliance e governança.

📦 Requisitos
Python 3.9 ou superior

Dependências principais:

pandas

requests

openpyxl

python-dotenv (para variáveis de ambiente)

Verifique todos os requisitos em requirements.txt

⚙️ Configuração (.env)
Exemplo de .env:


CLIENT_ID=seu_client_id
CLIENT_SECRET=seu_client_secret
Nunca compartilhe este arquivo publicamente!
O .gitignore já está configurado para não permitir o commit do .env.

⚠️ Observações
Os arquivos user.csv e atividade.csv devem ser baixados manualmente do SAC.

O sistema busca automaticamente os arquivos mais recentes para cada prefixo.

Para evitar bloqueios ou exclusões incorretas, revise a lista de inativos antes de acionar o modo de desativação automática.

A lógica de busca de usuários pelo email é necessária pois o filtro SCIM padrão do SAC não aceita filtro direto por campo emails.

🤝 Contribuindo
Contribuições são bem-vindas!
Abra uma issue ou envie um pull request para melhorias, novas integrações ou exemplos de uso.

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

💡 Avisos Finais
Esta automação foi criada para auxiliar equipes de TI, governança e compliance a manterem a base de usuários do SAC segura, eficiente e alinhada com as melhores práticas de segurança e auditoria.
Use por sua conta e risco! Sempre valide manualmente os relatórios antes de efetuar desativações em massa.
""")
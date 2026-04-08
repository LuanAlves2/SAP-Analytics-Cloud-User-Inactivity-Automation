import requests
import pandas as pd
from io import StringIO

def get_token(OAUTH_TOKEN_URL, CLIENT_ID, CLIENT_SECRET):
    resp = requests.post(
        OAUTH_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    resp.raise_for_status()
    return resp.json()['access_token']

def get_csrf_token(CSRF_URL, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "x-sap-sac-custom-auth": "true",
        "x-csrf-token": "fetch",
    }
    resp = requests.get(CSRF_URL, headers=headers)
    resp.raise_for_status()
    csrf_token = resp.headers.get("x-csrf-token")
    cookies = resp.cookies.get_dict()
    if not csrf_token:
        raise Exception("CSRF token não encontrado na resposta!")
    return csrf_token, cookies

def buscar_todos_usuarios(SAC_SCIM_API_URL, token):
    """Busca todos os usuarios via SCIM API e retorna um DataFrame no mesmo formato do user.csv exportado."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "x-sap-sac-custom-auth": "true"
    }
    usuarios = []
    start_index = 1
    count = 100
    while True:
        params = {"startIndex": start_index, "count": count}
        resp = requests.get(SAC_SCIM_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("Resources", [])
        if not batch:
            break
        usuarios.extend(batch)
        total = data.get("totalResults", 0)
        print(f"Obtidos {len(usuarios)}/{total} usuarios via SCIM...")
        if len(usuarios) >= total:
            break
        start_index += count

    # Debug: mostra todos os campos do primeiro usuario para identificar mapeamento
    if usuarios:
        print("\n[DEBUG] Campos do primeiro usuario SCIM:")
        primeiro = usuarios[0]
        for chave, valor in primeiro.items():
            if chave != "schemas":
                print(f"  {chave}: {valor}")
        print()

    registros = []
    for u in usuarios:
        emails = u.get("emails", [])
        email = emails[0].get("value", "") if emails else ""
        registros.append({
            "USER_NAME": u.get("id", u.get("userName", "")),
            "FIRST_NAME": u.get("name", {}).get("givenName", ""),
            "LAST_NAME": u.get("name", {}).get("familyName", ""),
            "DISPLAY_NAME": u.get("displayName", ""),
            "EMAIL": email,
            "IS_USER_DEACTIVATED": "true" if not u.get("active", True) else "",
        })
    return pd.DataFrame(registros)


def exportar_atividades(SAC_ACTIVITIES_URL, token, csrf_url, data_inicio=None):
    """Exporta o log de atividades via POST + CSRF token. Retorna DataFrame com todas as paginas."""
    # Obter CSRF token e cookies
    csrf_token, cookies = get_csrf_token(csrf_url, token)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-csrf-token": csrf_token,
        "x-sap-sac-custom-auth": "true"
    }

    todas_linhas = []
    page_index = 1

    while True:
        params = {
            "pageIndex": page_index,
            "sortKey": "Timestamp",
            "sortDescending": "false"
        }
        if data_inicio:
            resp = requests.post(
                SAC_ACTIVITIES_URL, headers=headers,
                params=params, json={"from": data_inicio}, cookies=cookies
            )
        else:
            resp = requests.post(
                SAC_ACTIVITIES_URL, headers=headers,
                params=params, data="", cookies=cookies
            )
        resp.raise_for_status()

        texto = resp.text.strip()
        if not texto:
            break

        # Pula linha descritiva se existir (ex: "User Activities")
        linhas = texto.split("\n")
        if linhas and "Object Type" not in linhas[0]:
            texto = "\n".join(linhas[1:])

        df_page = pd.read_csv(StringIO(texto), dtype=str, on_bad_lines="skip", engine="python")
        df_page.columns = [col.strip() for col in df_page.columns]
        todas_linhas.append(df_page)

        total_pages = int(resp.headers.get("epm-page-count", "1"))
        print(f"Atividades: pagina {page_index}/{total_pages}")

        if page_index >= total_pages:
            break
        page_index += 1

    df = pd.concat(todas_linhas, ignore_index=True) if todas_linhas else pd.DataFrame()
    print(f"Obtidas {len(df)} linhas de atividades via API.")
    return df


def buscar_usuario_por_email(SAC_SCIM_API_URL, token, email):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "x-sap-sac-custom-auth": "true"
    }
    usuarios = []
    start_index = 1
    count = 100
    while True:
        params = {"startIndex": start_index, "count": count}
        resp = requests.get(SAC_SCIM_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("Resources", [])
        if not batch:
            break
        for user in batch:
            emails = user.get("emails", [])
            for email_obj in emails:
                if email_obj.get("value", "").lower() == email.lower():
                    return user
        usuarios.extend(batch)
        total = data.get("totalResults", 0)
        if len(usuarios) >= total:
            break
        start_index += count
    return None

def get_user_object(SAC_SCIM_API_URL, token, user_id, cookies):
    url = f"{SAC_SCIM_API_URL}/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-sap-sac-custom-auth": "true",
        "Accept": "application/json"
    }
    resp = requests.get(url, headers=headers, cookies=cookies)
    resp.raise_for_status()
    return resp.json()

def desativar_usuario(SAC_SCIM_API_URL, token, user_id, csrf_token, cookies):
    user_obj = get_user_object(SAC_SCIM_API_URL, token, user_id, cookies)
    user_obj.pop("meta", None)
    user_obj["active"] = False
    user_obj["id"] = user_id
    url = f"{SAC_SCIM_API_URL}/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "x-sap-sac-custom-auth": "true",
        "Content-Type": "application/json",
        "x-csrf-token": csrf_token
    }
    resp = requests.put(url, headers=headers, json=user_obj, cookies=cookies)
    print("Payload enviado (debug):", user_obj)
    if resp.status_code in [200, 204]:
        print(f"✅ Usuário {user_id} desativado com sucesso!")
    else:
        print(f"❌ Erro ao desativar {user_id}: {resp.status_code} {resp.text}")

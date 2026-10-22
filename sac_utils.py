import requests
import pandas as pd
from io import StringIO

from config import HTTP_TIMEOUT


def get_token(OAUTH_TOKEN_URL, CLIENT_ID, CLIENT_SECRET):
    resp = requests.post(
        OAUTH_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_csrf_token(CSRF_URL, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "x-sap-sac-custom-auth": "true",
        "x-csrf-token": "fetch",
    }
    resp = requests.get(CSRF_URL, headers=headers, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    csrf_token = resp.headers.get("x-csrf-token")
    cookies = resp.cookies.get_dict()
    if not csrf_token:
        raise Exception("CSRF token nao encontrado na resposta!")
    return csrf_token, cookies


def _headers_scim(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "x-sap-sac-custom-auth": "true",
    }


def _iterar_usuarios_scim(SAC_SCIM_API_URL, token, count=100):
    """Percorre todas as paginas da SCIM API e gera os usuarios um a um."""
    start_index = 1
    obtidos = 0
    while True:
        params = {"startIndex": start_index, "count": count}
        resp = requests.get(SAC_SCIM_API_URL, headers=_headers_scim(token), params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("Resources", [])
        if not batch:
            break
        obtidos += len(batch)
        total = data.get("totalResults", 0)
        print(f"Obtidos {obtidos}/{total} usuarios via SCIM...")
        for u in batch:
            yield u
        if obtidos >= total:
            break
        start_index += count


def buscar_todos_usuarios(SAC_SCIM_API_URL, token):
    """Busca todos os usuarios via SCIM API e retorna um DataFrame."""
    registros = []
    for u in _iterar_usuarios_scim(SAC_SCIM_API_URL, token):
        emails = u.get("emails") or []
        email = (emails[0].get("value") or "") if emails else ""
        nome = u.get("name") or {}
        registros.append({
            "USER_NAME": u.get("id") or u.get("userName", ""),
            "FIRST_NAME": nome.get("givenName", ""),
            "LAST_NAME": nome.get("familyName", ""),
            "DISPLAY_NAME": u.get("displayName", ""),
            "EMAIL": email,
            "IS_USER_DEACTIVATED": "true" if not u.get("active", True) else "",
            "CRIADO_EM": (u.get("meta") or {}).get("created", ""),
        })
    colunas = ["USER_NAME", "FIRST_NAME", "LAST_NAME", "DISPLAY_NAME", "EMAIL", "IS_USER_DEACTIVATED", "CRIADO_EM"]
    return pd.DataFrame(registros, columns=colunas)


def exportar_atividades(SAC_ACTIVITIES_URL, token, csrf_url, data_inicio=None):
    """Exporta o log de atividades via POST + CSRF token. Retorna DataFrame com todas as paginas."""
    csrf_token, cookies = get_csrf_token(csrf_url, token)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-csrf-token": csrf_token,
        "x-sap-sac-custom-auth": "true",
    }

    todas_linhas = []
    page_index = 1

    while True:
        params = {
            "pageIndex": page_index,
            "sortKey": "Timestamp",
            "sortDescending": "false",
        }
        kwargs = {"json": {"from": data_inicio}} if data_inicio else {"data": ""}
        resp = requests.post(
            SAC_ACTIVITIES_URL, headers=headers, params=params, cookies=cookies,
            timeout=HTTP_TIMEOUT, **kwargs
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
    """Procura um usuario pelo email percorrendo a SCIM API. Retorna o objeto ou None."""
    email = (email or "").lower()
    if not email:
        return None
    for user in _iterar_usuarios_scim(SAC_SCIM_API_URL, token):
        for email_obj in user.get("emails") or []:
            if (email_obj.get("value") or "").lower() == email:
                return user
    return None


def get_user_object(SAC_SCIM_API_URL, token, user_id, cookies=None):
    url = f"{SAC_SCIM_API_URL}/{user_id}"
    resp = requests.get(url, headers=_headers_scim(token), cookies=cookies, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def desativar_usuario(SAC_SCIM_API_URL, token, user_id, csrf_token, cookies):
    """Desativa o usuario (active=false) via PUT.

    Retorna (status, mensagem), onde status e um de:
    "desativado", "ja_desativado", "nao_encontrado", "erro".
    Nunca lanca excecao: a falha de um usuario nao deve interromper os demais.
    """
    try:
        try:
            user_obj = get_user_object(SAC_SCIM_API_URL, token, user_id, cookies)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return "nao_encontrado", "Usuario nao encontrado no SAC"
            raise

        if not user_obj.get("active", True):
            return "ja_desativado", "Usuario ja estava desativado"

        user_obj.pop("meta", None)
        user_obj["active"] = False
        user_obj["id"] = user_id
        url = f"{SAC_SCIM_API_URL}/{user_id}"
        headers = {
            **_headers_scim(token),
            "Content-Type": "application/json",
            "x-csrf-token": csrf_token,
        }
        resp = requests.put(url, headers=headers, json=user_obj, cookies=cookies, timeout=HTTP_TIMEOUT)
        if resp.status_code in (200, 204):
            return "desativado", "Desativado com sucesso"
        return "erro", f"HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as e:
        return "erro", f"{type(e).__name__}: {e}"

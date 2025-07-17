import requests

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

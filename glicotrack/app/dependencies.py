from fastapi import Request, HTTPException, status
from app.services.supabase_client import get_supabase, get_supabase_with_token


def get_current_user(request: Request) -> dict:
    """
    Lê o token de sessão do cookie e valida com o Supabase.
    Retorna os dados do usuário logado ou redireciona para login.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    try:
        client = get_supabase()
        user_response = client.auth.get_user(access_token)
        if not user_response or not user_response.user:
            print("DEPENDENCIA: user_response vazio")
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/login"},
            )
        print(f"DEPENDENCIA OK: {user_response.user.email}")
        return {"user": user_response.user, "access_token": access_token}
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEPENDENCIA ERRO: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )

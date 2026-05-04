from supabase import create_client, Client
from app.config import get_settings

_client: Client | None = None
_admin_client: Client | None = None


def get_supabase() -> Client:
    """Cliente com anon key — usado apenas para autenticação (login/cadastro)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def get_supabase_admin() -> Client:
    """Cliente com service key — usado para operações no banco (ignora RLS)."""
    global _admin_client
    if _admin_client is None:
        settings = get_settings()
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client


def get_supabase_with_token(access_token: str) -> Client:
    """Mantido por compatibilidade — redireciona para o cliente admin."""
    return get_supabase_admin()

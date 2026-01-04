"""
Error Localization - Localized error messages for better user experience.
"""

ERROR_MESSAGES = {
    "file_not_found": {
        "en": "File not found: {path}. Search for similar files?",
        "pt": "Arquivo nao encontrado: {path}. Buscar arquivos similares?",
    },
    "tool_not_found": {
        "en": "Unknown tool: {tool}",
        "pt": "Ferramenta desconhecida: {tool}",
    },
    "ambiguous_request": {
        "en": "I'm not sure what you mean. Could you clarify?",
        "pt": "Nao tenho certeza do que voce quer. Pode esclarecer?",
    },
    "permission_denied": {
        "en": "Permission denied: {path}. Try running with sudo?",
        "pt": "Permissao negada: {path}. Tente rodar com sudo?",
    },
    "execution_failed": {
        "en": "Execution failed: {error}",
        "pt": "Execucao falhou: {error}",
    },
}


def get_error_message(key: str, lang: str = "en", **kwargs) -> str:
    """Get localized error message."""
    messages = ERROR_MESSAGES.get(key, {})
    message = messages.get(lang, messages.get("en", "Unknown error"))
    return message.format(**kwargs)

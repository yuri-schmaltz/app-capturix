class LinSnipperError(Exception):
    """Erro base da aplicação."""


class CaptureError(LinSnipperError):
    """Falha em alguma operação de captura de tela."""


class ConfigError(LinSnipperError):
    """Problema ao carregar/salvar configuração."""

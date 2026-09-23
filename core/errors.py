class JarvisError(Exception):
    """Erro base do assistente."""


class LLMError(JarvisError):
    """Erro ao gerar uma resposta via IA."""


class SecurityError(JarvisError):
    """Erro de autorização ou segurança."""


class SkillError(JarvisError):
    """Erro de execução de uma Skill."""

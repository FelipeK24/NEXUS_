class JarvisError(Exception):
    """Erro base do assistente."""


class LLMError(JarvisError):
    """Erro ao gerar uma resposta via IA."""


class SecurityError(JarvisError):
    """Erro de autorização ou segurança."""


class PlanningError(JarvisError):
    """The request could not be transformed into a safe plan."""


class SkillError(JarvisError):
    """Erro de execução de uma Skill."""

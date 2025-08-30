# .github/validator/rules/base.py
class ValidationRule:
    def __init__(self, name):
        self.name = name

    def run(self, repo, pr, service_name, rules_cfg):
        """
        Ejecuta la validación.
        Debe retornar lista de observaciones (strings).
        """
        raise NotImplementedError

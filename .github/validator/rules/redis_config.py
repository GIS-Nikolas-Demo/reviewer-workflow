# .github/validator/rules/redis_config.py
import os, yaml
from .base import ValidationRule

class RedisRule(ValidationRule):
    def __init__(self):
        super().__init__("Redis Config")

    def run(self, repo, pr, service_name, rules_cfg):
        print(f"🔍 Ejecutando regla: {self.name}")
        observations = []
        redis_rules = rules_cfg.get("redis", {})
        redis_path_template = redis_rules.get("path_template", "redis-configs/{service}.yml")
        required_keys = redis_rules.get("required_keys", [])
        optional_keys = redis_rules.get("optional_keys", [])

        config_repo_dir = os.getenv("CONFIG_REPO_DIR", "config-repo")
        
        redis_cfg_path = os.path.join(config_repo_dir, redis_path_template.replace("{service}", service_name))

        if not os.path.exists(config_repo_dir):
            observations.append("⚠️ No se pudo leer el repo de configuración.")
            return observations
        if not os.path.exists(redis_cfg_path):
            observations.append(f"❌ No existe `{redis_cfg_path}`.")
            return observations

        try:
            with open(redis_cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)

            errors_required = self.validate_keys(cfg, required_keys)
            if errors_required:
                observations.append("❌ Problemas en claves obligatorias:\n" + "\n".join(errors_required))
            else:
                observations.append(f"✅ Claves obligatorias válidas en `{redis_cfg_path}`.")

            errors_optional = self.validate_keys(cfg, optional_keys)
            if errors_optional:
                observations.append("⚠️ Problemas en claves opcionales:\n" + "\n".join(errors_optional))

        except Exception as e:
            observations.append(f"⚠️ Error leyendo `{redis_cfg_path}`: {e}")

        return observations

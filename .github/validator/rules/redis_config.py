# .github/validator/rules/redis_config.py
import os, yaml
from .base import ValidationRule

class RedisRule(ValidationRule):
    def __init__(self):
        super().__init__("Redis Config")

    def run(self, repo, pr, service_name, rules_cfg):
        observations = []
        redis_rules = rules_cfg.get("redis", {})
        redis_path_template = redis_rules.get("path_template", "redis-configs/{service}.yml")
        redis_required = redis_rules.get("required_keys", [])

        config_repo_dir = os.getenv("CONFIG_REPO_DIR", "config-repo")
        redis_cfg_relpath = redis_path_template.replace("{service}", service_name)
        redis_cfg_path = os.path.join(config_repo_dir, redis_cfg_relpath)

        if not os.path.exists(config_repo_dir):
            observations.append("⚠️ **Redis**: No se pudo leer el repo de configuración (fork sin secretos).")
        elif not os.path.exists(redis_cfg_path):
            observations.append(f"❌ **Redis**: No existe `{redis_cfg_relpath}` en el repo de configuración.")
        else:
            try:
                with open(redis_cfg_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                missing_keys = [k for k in redis_required if not self._extract(cfg, k)]
                if missing_keys:
                    observations.append("❌ **Redis**: Faltan claves requeridas:\n" + "\n".join([f"- `{k}`" for k in missing_keys]))
                else:
                    observations.append(f"✅ **Redis**: Configuración válida en `{redis_cfg_relpath}`.")
            except Exception as e:
                observations.append(f"⚠️ **Redis**: Error leyendo `{redis_cfg_relpath}`: {e}")
        return observations

    def _extract(self, dct, dotted_key):
        cur = dct
        for k in dotted_key.split("."):
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

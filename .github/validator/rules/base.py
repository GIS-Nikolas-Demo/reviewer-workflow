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

    # -------------------------
    # Reutilizables para todos los módulos
    # -------------------------
    def validate_key(self, cfg, key_def):
        """Valida una sola clave según su definición"""
        key = key_def.get("key")
        val_type = key_def.get("type", "string")
        required = key_def.get("required", False)
        min_val = key_def.get("min")
        max_val = key_def.get("max")

        val = self._extract(cfg, key)

        if val is None:
            if required:
                return f"- `{key}` (faltante)"
            else:
                return None

        if val_type == "int":
            try:
                val_int = int(val)
                if min_val is not None and val_int < min_val:
                    return f"- `{key}`={val_int} < mínimo {min_val}"
                if max_val is not None and val_int > max_val:
                    return f"- `{key}`={val_int} > máximo {max_val}"
            except Exception:
                return f"- `{key}` tiene valor no numérico: `{val}`"

        elif val_type == "string":
            if not isinstance(val, str):
                return f"- `{key}` debería ser string, pero tiene: `{val}`"

        elif val_type == "bool":
            if not isinstance(val, bool):
                if str(val).lower() not in ["true", "false"]:
                    return f"- `{key}` debería ser booleano, pero tiene: `{val}`"

        else:
            return f"- `{key}` tipo desconocido: {val_type}"

        return None

    def validate_keys(self, cfg, keys):
        """Valida un conjunto de claves y retorna lista de errores"""
        return [e for e in (self.validate_key(k) for k in keys) if e]

    def _extract(self, dct, dotted_key):
        """Extrae valor de dict anidado usando notación punto"""
        cur = dct
        for k in dotted_key.split("."):
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur

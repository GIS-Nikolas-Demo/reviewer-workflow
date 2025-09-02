# .github/validator/rules/circuitbreaker.py
import os
import yaml
import fnmatch

from .base import ValidationRule

class CircuitBreakerRule(ValidationRule):
    def __init__(self):
        super().__init__("Circuit Breaker")

    def run(self, repo, pr, service_name, module_cfg):
        observations = []
        observations.append("🛠️ Validación de reglas Circuit Breaker")

        # --- 1) Validación de código Java (anotaciones en controladores) ---
        print(module_cfg)
        java_cfg = (module_cfg or {}).get("java", {})
        controller_markers = java_cfg.get("controller_markers", [])
        annotations_required_any = java_cfg.get("annotations_required_any", [])
        exclude_globs = java_cfg.get("exclude_globs", [])
        print(annotations_required_any)
        missing_annotations = self._validate_java_annotations(
            controller_markers,
            annotations_required_any,
            exclude_globs
        )

        if missing_annotations:
            observations.append(
                "❌ **Circuit Breaker (código)**: Faltan anotaciones en clases controladoras:\n"
                + "\n".join([f"- `{p}`" for p in missing_annotations])
                + ("\n> Debe incluir al menos una de: " + ", ".join(annotations_required_any) if annotations_required_any else "")
            )
        else:
            observations.append("✅ **Circuit Breaker (código)**: Anotaciones presentes en controladores.")

        # --- 2) (Opcional) Validación de configuración YAML en repo externo ---
        config_repo_dir = os.getenv("CONFIG_REPO_DIR", "config-repo")
        path_template = (module_cfg or {}).get("path_template")  # puede ser None
        required_keys = (module_cfg or {}).get("required_keys", [])
        optional_keys = (module_cfg or {}).get("optional_keys", [])

        if path_template:
            cfg_relpath = path_template.replace("{service}", service_name)
            cfg_path = os.path.join(config_repo_dir, cfg_relpath)

            if not os.path.exists(config_repo_dir):
                observations.append("⚠️ **Circuit Breaker (config)**: No se pudo leer el repo de configuración.")
            elif not os.path.exists(cfg_path):
                observations.append(f"❌ **Circuit Breaker (config)**: No existe `{cfg_relpath}` en el repo de configuración.")
            else:
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}

                    # Reutiliza el validador genérico de la clase base
                    req_errors = self.validate_keys(cfg, required_keys)
                    opt_errors = self.validate_keys(cfg, optional_keys)

                    if req_errors:
                        observations.append(
                            "❌ **Circuit Breaker (config)**: Problemas en claves obligatorias:\n" +
                            "\n".join(req_errors)
                        )
                    else:
                        observations.append(f"✅ **Circuit Breaker (config)**: Claves obligatorias válidas en `{cfg_relpath}`.")

                    if opt_errors:
                        observations.append(
                            "⚠️ **Circuit Breaker (config)**: Problemas en claves opcionales:\n" +
                            "\n".join(opt_errors)
                        )

                except Exception as e:
                    observations.append(f"⚠️ **Circuit Breaker (config)**: Error leyendo `{cfg_relpath}`: {e}")

        return observations

    # --------- Helpers ----------

    def _list_all_java_files(self):
        files = []
        for root, _, filenames in os.walk("."):
            for name in filenames:
                if name.endswith(".java"):
                    files.append(os.path.join(root, name))
        return files

    def _is_excluded(self, path, exclude_globs):
        # Permite exclusiones tipo glob (src/test/**, **/generated/**)
        return any(fnmatch.fnmatch(path, pattern) for pattern in exclude_globs)

    def _validate_java_annotations(self, controller_markers, annotations_required_any, exclude_globs):
        """
        Devuelve lista de archivos .java que parecen controladores y NO tienen ninguna de las
        anotaciones requeridas.
        """
        if not controller_markers:
            return []  # si no definiste marcadores, no marcamos nada

        missing = []
        for path in self._list_all_java_files():
            if exclude_globs and self._is_excluded(path, exclude_globs):
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # ¿es controlador?
                if any(marker in content for marker in controller_markers):
                    # ¿tiene alguna anotación requerida?
                    if annotations_required_any and not any(a in content for a in annotations_required_any):
                        missing.append(path)
            except Exception:
                # Ignora archivos que no se puedan leer, no fallamos el build por esto
                continue

        return missing

# .github/validator/rules/java_circuitbreaker.py
import os
from .base import ValidationRule

class CircuitBreakerRule(ValidationRule):
    def __init__(self):
        super().__init__("Circuit Breaker en Java")

    def run(self, repo, pr, service_name, rules_cfg):
        observations = []
        ann_required_any = rules_cfg.get("java", {}).get("annotations_required_any", [])
        controller_markers = rules_cfg.get("java", {}).get("controller_markers", [])
        print(f"▶ Reglas: {ann_required_any}")
        java_files = []
        for root, _, files in os.walk("."):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(root, f))

        missing_cb = []
        print(f"▶ Archivos Java a escanear: {java_files}")
        for path in java_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if any(m in content for m in controller_markers) and not any(a in content for a in ann_required_any):
                    missing_cb.append(path)
            except Exception as e:
                observations.append(f"⚠️ No se pudo analizar `{path}`: {e}")

        if missing_cb:
            observations.append(
                "❌ **Circuit Breaker**: Faltan anotaciones en:\n" +
                "\n".join([f"- `{p}`" for p in missing_cb]) +
                "\n> Debe incluir alguna de: " + ", ".join(ann_required_any)
            )
        else:
            observations.append("✅ **Circuit Breaker**: Todas las clases cumplen.")
        return observations

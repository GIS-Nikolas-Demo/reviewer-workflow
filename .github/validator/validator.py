# validator.py
import os, sys, yaml, importlib
from github import Github

from dependency_loader import get_dependencies_from_pom
from rule_loader import get_rules_for_dependencies

# --- GitHub Context ---
token = os.getenv("GITHUB_TOKEN")
repo_full = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("GITHUB_PR_NUMBER"))
service_name = os.getenv("MICROSERVICE_NAME")
rules_path = os.getenv("RULES_PATH", ".org-reviewer")

g = Github(token)
repo = g.get_repo(repo_full)
pr = repo.get_pull(pr_number)

# --- Main ---
if not service_name:
    service_name = repo_full.split("/", 1)[1]

# 1. Leer dependencias del pom.xml
dependencies = get_dependencies_from_pom()
print("📦 Dependencias detectadas:", dependencies)

# 2. Seleccionar reglas dinámicamente según dependencias
rules = get_rules_for_dependencies(dependencies, rules_path)
print("🛠️ Reglas activas:", rules.keys())

observations = []

# 3. Ejecutar cada regla especializada
for file_name, file_rules in rules.items():
    module_name = file_name.replace("-rules.yml", "")
    print(f"\n🔧 Procesando módulo: {module_name}")

    try:
        # Import dinámico: .github/validator/rules/redis_config.py => rules.redis_config
        rule_module = importlib.import_module(f".rules.{module_name}_config", package="validator")
        rule_class = [cls for name, cls in rule_module.__dict__.items()
                      if isinstance(cls, type) and cls.__name__.endswith("Rule")][0]

        rule_instance = rule_class()
        obs = rule_instance.run(repo, pr, service_name, {module_name: {"rules": file_rules}})
        observations.extend(obs)

    except ModuleNotFoundError:
        print(f"⚠️ No se encontró implementación de regla para {module_name}, usando fallback.")
        # Aquí podrías hacer una validación genérica mínima
    except Exception as e:
        observations.append(f"⚠️ Error ejecutando regla {module_name}: {e}")

# --- Componer comentario ---
header = "🔎 **Revisor de Organización – Reporte Automático**"
body = header + "\n\n" + ("\n\n".join(observations) if observations else "✅ No se encontraron observaciones.")

has_errors = any(obs.startswith("❌") for obs in observations)

if has_errors:
    pr.create_review(body=body, event="REQUEST_CHANGES")
    sys.exit(1)
else:
    pr.create_review(body=body, event="COMMENT")
    sys.exit(0)

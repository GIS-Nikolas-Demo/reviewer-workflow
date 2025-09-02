# validator.py
import os, sys, yaml
from github import Github
from rules.redis import RedisRule
from rules.circuitbreaker import CircuitBreakerRule

# Registro de reglas disponibles por módulo
RULES_REGISTRY = {
    "redis": RedisRule,
    "circuitbreaker": CircuitBreakerRule,
}

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

# 2. Obtener configuraciones activas según dependencias
rules_cfg = get_rules_for_dependencies(dependencies, rules_path)


# 4. Seleccionar reglas dinámicamente según rules_cfg
rules = [
    RULES_REGISTRY[module]()  # instancia vacía
    for module in rules_cfg
    if module in RULES_REGISTRY
]

print("🛠️ Reglas aplicadas:", list(rules_cfg.keys()))

# 5. Ejecutar cada regla especializada con **su propia configuración**
observations = []
for module, rule in zip(rules_cfg.keys(), rules):
    print(f"▶ Ejecutando regla: {rule.name}")
    obs = rule.run(repo, pr, service_name, rules_cfg[module])  # solo config de su módulo
    observations.extend(obs)



# --- Componer comentario ---
header = "🔎 **Revisor Buenas Practicas y lineamiento - COE Ing de Sw **"
body = header + "\n\n" + ("\n\n".join(observations) if observations else "✅ No se encontraron observaciones.")

has_errors = any(obs.startswith("❌") for obs in observations)

if has_errors:
    pr.create_review(body=body, event="REQUEST_CHANGES")
    sys.exit(1)
else:
    pr.create_review(body=body, event="COMMENT")
    sys.exit(0)

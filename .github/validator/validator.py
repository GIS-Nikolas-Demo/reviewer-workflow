# validator.py
import os, sys, yaml
from github import Github

# --- Importar loaders ---
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


def load_yaml_file(path):
    """Carga un archivo YAML y lo retorna como dict"""
    if not os.path.exists(path):
        print(f"⚠️ No se encontró archivo de reglas en: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_rule_files(base_path=".org-reviewer"):
    """Detecta todos los archivos {modulo}-rules.yml en la carpeta .org-reviewer"""
    if not os.path.exists(base_path):
        return []

    return [
        os.path.join(base_path, f)
        for f in os.listdir(base_path)
        if f.endswith("-rules.yml")
    ]


# --- Main ---
if not service_name:
    service_name = repo_full.split("/", 1)[1]

# 1. Leer dependencias del pom.xml
dependencies = get_dependencies_from_pom()
print("📦 Dependencias detectadas:", dependencies)

# 2. Detectar archivos de reglas disponibles
rule_files = detect_rule_files(rules_path)
print("📑 Archivos de reglas detectados:", rule_files)

# 3. Seleccionar reglas dinámicamente según dependencias
rules = get_rules_for_dependencies(dependencies)
print("🛠️ Reglas activas:", [r.name for r in rules])

observations = []

# 4. Ejecutar cada regla contra su archivo de configuración
for rule_file in rule_files:
    module_name = os.path.basename(rule_file).replace("-rules.yml", "")
    print(f"\n🔧 Procesando módulo: {module_name}")

    rules_cfg = load_yaml_file(rule_file)

    for rule in rules:
        print(f"▶ Ejecutando regla: {rule.name} en módulo {module_name}")
        obs = rule.run(repo, pr, service_name, rules_cfg)
        observations.extend(obs)


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

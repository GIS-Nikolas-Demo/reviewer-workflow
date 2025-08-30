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

def load_yaml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def detect_rule_files(base_path):
    rule_files = []
    for f in os.listdir(base_path):
        if f.endswith("-rules.yml") or f == "rules.yml":
            rule_files.append(os.path.join(base_path, f))
    return rule_files

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
rules = get_rules_for_dependencies(dependencies,rules_path)
print("🛠️ Reglas activas:", rules.keys)  # ahora muestra por archivo

observations = []

# 4. Ejecutar cada regla contra su archivo de configuración
for file_name, file_rules in rules.items():
    module_name = file_name.replace("-rules.yml", "")
    print(f"\n🔧 Procesando módulo: {module_name}")
    print(f"\n🔧 Reglas: {file_rules}")

    # file_rules ya es un dict con listas: required_keys, optional_keys
    for key_def in file_rules.get("required_keys", []):
        key = key_def["key"]
        if key_def.get("required", False):
            # ejemplo de validación mínima
            observations.append(
                f"❌ Falta key obligatoria: {key} en {module_name}"
            )

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

import os, re, yaml, sys
from github import Github

# --- Env vars ---
token = os.getenv("GITHUB_TOKEN")
repo_full = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("GITHUB_PR_NUMBER"))
service_name = os.getenv("MICROSERVICE_NAME")
rules_path = os.getenv("RULES_PATH", ".org-reviewer/rules.yml")
config_repo_dir = os.getenv("CONFIG_REPO_DIR", "config-repo")

g = Github(token)
repo = g.get_repo(repo_full)
pr = repo.get_pull(pr_number)
#actor = g.get_user().login

# --- Utilidades ---
def load_yaml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_repo_name_as_service():
    # ms-orders-api -> ms-orders-api
    return repo_full.split("/", 1)[1]

def list_changed_files_local_java():
    changed = []
    for f in pr.get_files():
        if f.status in ("added","modified","renamed") and f.filename.endswith(".java"):
            # asegurar que el path exista (checkout del HEAD)
            if os.path.exists(f.filename):
                changed.append(f.filename)
    return changed

def has_any(text, needles):
    return any(n in text for n in needles)

def extract_by_keys(dct, dotted_key):
    cur = dct
    for k in dotted_key.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

# --- Cargar reglas ---
rules = load_yaml_file(rules_path)
ann_required_any = rules.get("java", {}).get("annotations_required_any", [])
controller_markers = rules.get("java", {}).get("controller_markers", [])
redis_rules = rules.get("redis", {})
redis_path_template = redis_rules.get("path_template", "redis-configs/{service}.yml")
redis_required = redis_rules.get("required_keys", [])
redis_optional = redis_rules.get("optional_keys", [])

# --- Determinar service name ---
if not service_name:
    service_name = get_repo_name_as_service()

observations = []

# === Validación 1: Anotaciones Circuit Breaker en Java ===
java_files = list_changed_files_local_java()
missing_cb = []

for path in java_files:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if has_any(content, controller_markers) and not has_any(content, ann_required_any):
            missing_cb.append(path)
    except Exception as e:
        observations.append(f"⚠️ No se pudo analizar `{path}`: {e}")

if missing_cb:
    observations.append(
        "❌ **Circuit Breaker**: Faltan anotaciones en las siguientes clases controladoras:\n" +
        "\n".join([f"- `{p}`" for p in missing_cb]) +
        "\n> Asegura incluir alguna de: " + ", ".join(ann_required_any)
    )
else:
    observations.append("✅ **Circuit Breaker**: Las clases cambiadas cumplen con anotaciones requeridas.")

# === Validación 2: Config Redis cross-repo ===
redis_cfg_relpath = redis_path_template.replace("{service}", service_name)
redis_cfg_path = os.path.join(config_repo_dir, redis_cfg_relpath)

if not os.path.exists(config_repo_dir):
    observations.append("⚠️ **Redis**: No se pudo leer el repo de configuración. "
                        "Posible PR desde fork sin secretos. Se omitió esta validación.")
else:
    if not os.path.exists(redis_cfg_path):
        observations.append(f"❌ **Redis**: No existe `{redis_cfg_relpath}` en el repo de configuración.")
    else:
        try:
            cfg = load_yaml_file(redis_cfg_path)
            missing_keys = [k for k in redis_required if extract_by_keys(cfg, k) in (None, "")]
            if missing_keys:
                observations.append("❌ **Redis**: Faltan claves requeridas en "
                                    f"`{redis_cfg_relpath}`:\n" + "\n".join([f"- `{k}`" for k in missing_keys]))
            else:
                observations.append(f"✅ **Redis**: Configuración válida en `{redis_cfg_relpath}`.")
        except Exception as e:
            observations.append(f"⚠️ **Redis**: Error leyendo `{redis_cfg_relpath}`: {e}")

# --- Componer comentario general ---
header = "🔎 **Revisor de Organización – Reporte Automático**"
body = header + "\n\n" + "\n\n".join(observations)

# --- Publicar review general ---
has_errors = any(obs.startswith("❌") for obs in observations)

if has_errors:
    pr.create_review(body=body, event="REQUEST_CHANGES")
    print("Requested changes")
    sys.exit(1)
else:
    pr.create_review(body=body, event="COMMENT")
    print("Approved")
    sys.exit(0)

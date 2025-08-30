import os, sys, yaml
from github import Github
from rules.circuitbreaker import CircuitBreakerRule
from rules.redis_config import RedisRule

# --- GitHub Context ---
token = os.getenv("GITHUB_TOKEN")
repo_full = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("GITHUB_PR_NUMBER"))
service_name = os.getenv("MICROSERVICE_NAME")
rules_path = os.getenv("RULES_PATH", ".org-reviewer/rules.yml")

g = Github(token)
repo = g.get_repo(repo_full)
pr = repo.get_pull(pr_number)

def load_yaml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

rules_cfg = load_yaml_file(rules_path)
if not service_name:
    service_name = repo_full.split("/", 1)[1]

# --- Ejecutar reglas ---
rules = [CircuitBreakerRule(), RedisRule()]
observations = []
for rule in rules:
    print(f"▶ Ejecutando regla: {rule.name}")
    obs = rule.run(repo, pr, service_name, rules_cfg)
    observations.extend(obs)

# --- Componer comentario ---
header = "🔎 **Revisor de Organización – Reporte Automático**"
body = header + "\n\n" + "\n\n".join(observations)

has_errors = any(obs.startswith("❌") for obs in observations)

if has_errors:
    pr.create_review(body=body, event="REQUEST_CHANGES")
    sys.exit(1)
else:
    pr.create_review(body=body, event="COMMENT")
    sys.exit(0)

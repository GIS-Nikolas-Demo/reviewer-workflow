import os
import yaml

RULES_PATH = ".org-reviewer"

def get_rules_for_dependencies(dependencies):
    rules = {}

    for dep in dependencies:
        dep_name = dep.split(":")[-1].lower()  # ej: redis, kafka, sqlserver
        rule_file = os.path.join(RULES_PATH, f"{dep_name}-rules.yml")

        if os.path.exists(rule_file):
            with open(rule_file, "r") as f:
                data = yaml.safe_load(f)
                rules.update(data)  # agrega al diccionario global

    return rules

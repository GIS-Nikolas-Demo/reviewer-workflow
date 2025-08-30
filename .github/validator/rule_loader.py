import os
import yaml


def get_rules_for_dependencies(dependencies,rules_path):
    applied_rules = {}
    for file_name in os.listdir(rules_path):
        if file_name.endswith("-rules.yml"):
            file_path = os.path.join(rules_path, file_name)
            # nombre lógico de la regla quitando el sufijo
            rule_key = file_name.replace("-rules.yml", "")
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
                rules = data.get(rule_key, {})
                file_deps = rules.get("dependencies", [])

                # Verifica si alguna dependencia coincide
                if any(dep in file_deps for dep in dependencies):
                    applied_rules[file_name] = data  # guardamos por archivo
    print(f"\n🛠️ Reglas aplicadas: {applied_rules}")
    return applied_rules

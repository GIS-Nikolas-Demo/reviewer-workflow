import os
import yaml


def get_rules_for_dependencies(dependencies,rules_path):
    print("CWD:", os.getcwd())
    print("Files in CWD:", os.listdir("."))
    applied_rules = {}

    for file_name in os.listdir(rules_path):
        if file_name.endswith("-rules.yml"):
            file_path = os.path.join(rules_path, file_name)

            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

                file_deps = data.get("dependencies", [])
                file_rules = data.get("rules", {})

                # Verifica si alguna dependencia coincide
                if any(dep in file_deps for dep in dependencies):
                    applied_rules[file_name] = file_rules  # guardamos por archivo

    return applied_rules

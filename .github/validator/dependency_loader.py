import xml.etree.ElementTree as ET

def get_dependencies_from_pom(pom_path="pom.xml"):
    """
    Lee el archivo pom.xml y retorna la lista de dependencias como strings
    en formato groupId:artifactId.
    """
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}  # Namespace Maven

        dependencies = []
        for dep in root.findall(".//mvn:dependency", ns):
            group_id = dep.find("mvn:groupId", ns)
            artifact_id = dep.find("mvn:artifactId", ns)
            version = dep.find("mvn:version", ns)

            dep_str = f"{group_id.text if group_id is not None else ''}:{artifact_id.text if artifact_id is not None else ''}"
            dependencies.append(dep_str.lower())

        return dependencies
    except Exception as e:
        print(f"⚠️ No se pudo leer el pom.xml ({pom_path}): {e}")
        return []

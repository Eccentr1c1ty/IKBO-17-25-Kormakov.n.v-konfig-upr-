import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from urllib.request import urlopen

PROJECT_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_DIR / "config.json"


def validate_repository(repository, test_mode):
    """Проверить источник данных для выбранного режима."""
    if not isinstance(repository, str) or not repository.strip():
        raise ValueError("repository: укажи URL или путь к файлу")

    if test_mode:
        if not (PROJECT_DIR / repository).is_file():
            raise ValueError("repository: тестовый файл не найден")
        return

    url = urlsplit(repository)
    if url.scheme not in {"http", "https"} or not url.hostname:
        raise ValueError("repository: укажи корректный HTTP(S)-адрес")


def validate_config(config):
    """Проверить шесть параметров конфигурации."""
    if not isinstance(config, dict):
        raise ValueError("в config.json ожидается объект JSON")

    test_mode = config.get("test_mode")
    if not isinstance(test_mode, bool):
        raise ValueError("test_mode: укажи true или false")

    package_pattern = r"[A-Z]+" if test_mode else r"[\w.-]+:[\w.-]+"
    package = config.get("package")
    if not isinstance(package, str) or not re.fullmatch(
        package_pattern, package
    ):
        raise ValueError("package: укажи A–Z или groupId:artifactId по режиму")

    validate_repository(config.get("repository"), test_mode)

    version = config.get("version")
    if not isinstance(version, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._+-]*", version
    ):
        raise ValueError("version: укажи версию, например 4.13.2")

    output_file = config.get("output_file")
    if not isinstance(output_file, str) or not re.fullmatch(
        r'[^<>:"/\\|?*\x00-\x1f]+\.png', output_file, re.IGNORECASE
    ):
        raise ValueError("output_file: укажи имя файла с расширением .png")

    if not isinstance(config.get("filter_substring"), str):
        raise ValueError("filter_substring: укажи строку, можно пустую")


def parse_dependencies(xml_data):
    """Прочитать прямые зависимости из POM."""
    root = ET.fromstring(xml_data)
    namespace = root.tag.partition("}")[0] + "}" if "}" in root.tag else ""
    properties = {
        item.tag.removeprefix(namespace): (item.text or "").strip()
        for item in root.findall(f"{namespace}properties/*")
    }

    dependencies = []
    for item in root.findall(f"{namespace}dependencies/{namespace}dependency"):
        group = item.findtext(f"{namespace}groupId", "").strip()
        artifact = item.findtext(f"{namespace}artifactId", "").strip()
        version = item.findtext(f"{namespace}version", "").strip()
        scope = item.findtext(f"{namespace}scope", "compile").strip()
        version = re.sub(
            r"\$\{([^}]+)\}",
            lambda match: properties.get(match[1], match[0]),
            version,
        )
        dependencies.append((group, artifact, version, scope))
    return dependencies


def load_dependencies(repository, package, version):
    """Скачать POM по координатам и версии пакета."""
    group, artifact = package.split(":")
    group_path = group.replace(".", "/")
    filename = f"{artifact}-{version}.pom"
    path = f"{group_path}/{artifact}/{version}/{filename}"
    url = f"{repository.rstrip('/')}/{path}"

    with urlopen(url, timeout=10) as response:
        return parse_dependencies(response.read())


def main():
    """Прочитать настройки и вывести прямые зависимости."""
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
        validate_config(config)
    except (OSError, ValueError) as error:
        print(f"Ошибка конфигурации: {error}")
        return 1

    if config["test_mode"]:
        print("Тестовый граф будет добавлен на этапе 3.")
        return 1

    try:
        dependencies = load_dependencies(
            config["repository"], config["package"], config["version"]
        )
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Ошибка чтения POM: {error}")
        return 1

    print(f"Прямые зависимости {config['package']}:{config['version']}")
    for group, artifact, version, scope in dependencies:
        version_label = version or "версия не указана в POM"
        print(f"{group}:{artifact}:{version_label} ({scope})")

    if not dependencies:
        print("Прямых зависимостей нет.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
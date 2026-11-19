import argparse
from functools import partial
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from urllib.request import urlopen

from src.graph import read_test_graph, traverse
from src.render import save_diagram

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


def maven_neighbors(repository, node):
    """Получить зависимости compile/runtime выбранного пакета."""
    package, version = node.rsplit(":", 1)
    for group, artifact, release, scope in load_dependencies(
        repository, package, version
    ):
        if scope in {"compile", "runtime"}:
            if not release or "${" in release:
                package_id = f"{group}:{artifact}"
                raise ValueError(f"Не определена версия {package_id}")
            yield f"{group}:{artifact}:{release}"


def build_graph(config):
    """Выбрать источник данных и построить граф."""
    package = config["package"]
    repository = config["repository"]
    if config["test_mode"]:
        source = read_test_graph(PROJECT_DIR / repository)
        if package not in source:
            raise ValueError(f"Тестовый пакет {package} не найден.")
        root = package
        neighbors = source.__getitem__
    else:
        root = f"{package}:{config['version']}"
        neighbors = partial(maven_neighbors, repository)

    def excluded(node):
        """Сравнить подстроку с именем пакета без версии."""
        fragment = config["filter_substring"]
        name = node if config["test_mode"] else node.rsplit(":", 1)[0]
        return bool(fragment) and fragment in name

    return traverse(root, neighbors, excluded)


def show_graph(graph, cycles):
    """Показать список смежности и обнаруженные циклы."""
    for node, targets in graph.items():
        print(f"{node} -> {', '.join(targets) or '—'}")
    for node, target in cycles:
        print(f"Цикл: ребро {node} -> {target} замыкает путь DFS")
    if not graph:
        print("Граф пуст: начальный пакет исключён фильтром.")


def main():
    """Прочитать конфигурацию и выполнить анализ."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("config", nargs="?", type=Path, default=CONFIG_FILE)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        validate_config(config)
        graph, _, cycles = build_graph(config)
        show_graph(graph, cycles)
        png_path = PROJECT_DIR / "output" / config["output_file"]
        mmd_path = save_diagram(graph, png_path)
        print(f"Mermaid: {mmd_path}")
        print(f"PNG: {png_path}")
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Ошибка: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


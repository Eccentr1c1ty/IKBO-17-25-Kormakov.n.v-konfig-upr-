import json
import re
from pathlib import Path
from urllib.parse import urlsplit

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


def main():
    """Прочитать конфигурацию и напечатать её настройки."""
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
        validate_config(config)
    except (OSError, ValueError) as error:
        print(f"Ошибка конфигурации: {error}")
        return 1

    for key in (
        "package", "repository", "test_mode", "version",
        "output_file", "filter_substring",
    ):
        print(f"{key}={config[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Формирование Mermaid и экспорт диаграммы через Mermaid CLI."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SPECIAL_LABEL_CHARS = frozenset('#"&<>\\\r\n')


def to_mermaid(graph):
    """Описать все вершины и рёбра в формате Mermaid."""
    names = {node: f"p{index}" for index, node in enumerate(graph)}
    lines = ["flowchart TD"]
    for node, alias in names.items():
        label = "".join(
            f"#{ord(char)};" if char in SPECIAL_LABEL_CHARS else char
            for char in node
        )
        lines.append(f'    {alias}["{label}"]')
    for node, targets in graph.items():
        lines.extend(f"    {names[node]} --> {names[item]}" for item in targets)
    return "\n".join(lines) + "\n"


def render_command():
    """Выбрать доступный Mermaid CLI."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        tools = Path(local_app_data) / "MavenVisualizerTools"
        entry = tools / "node_modules/@mermaid-js/mermaid-cli/src/cli.js"
        node_path = tools / "node.path"
        if node_path.is_file():
            node = node_path.read_text(encoding="utf-8").strip()
        else:
            node = shutil.which("node")
        edge = tools / "puppeteer.json"
        if node and Path(node).is_file() and entry.is_file():
            if not edge.is_file():
                raise ValueError("Конфигурация браузера Mermaid отсутствует.")
            return [node, str(entry), "-p", str(edge)]
    cli = shutil.which("mmdc")
    if cli is None:
        raise ValueError("Установи Mermaid CLI и добавь mmdc в PATH.")
    if os.name == "nt" and Path(cli).suffix.lower() in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "mmdc"]
    return [cli]


def save_diagram(graph, png_path):
    """Сохранить текст Mermaid и PNG, проверив результат рендера."""
    source = to_mermaid(graph)
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        (temporary / "graph.mmd").write_text(source, encoding="utf-8")
        command = render_command()
        command.extend(["-i", "graph.mmd", "-o", "graph.png"])
        try:
            subprocess.run(command, cwd=temporary, check=True, timeout=120)
        except subprocess.SubprocessError as error:
            raise ValueError(f"Mermaid CLI: {error}") from error
        data = (temporary / "graph.png").read_bytes()
        if not data.startswith(PNG_SIGNATURE):
            raise ValueError("Mermaid CLI не создал корректный PNG.")

    png_path.parent.mkdir(parents=True, exist_ok=True)
    mmd_path = png_path.with_suffix(".mmd")
    mmd_path.write_text(source, encoding="utf-8")
    png_path.write_bytes(data)
    return mmd_path

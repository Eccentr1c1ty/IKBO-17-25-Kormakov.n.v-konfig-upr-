"""Источники рёбер и обход графа зависимостей."""

import json
import re


def read_test_graph(path):
    """Загрузить список смежности тестового репозитория."""
    graph = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(graph, dict):
        raise ValueError("Ожидается JSON-объект со списками зависимостей.")
    for name, targets in graph.items():
        if not valid_name(name) or not isinstance(targets, list):
            raise ValueError(f"Некорректное описание узла {name!r}.")
        for target in targets:
            if not valid_name(target) or target not in graph:
                raise ValueError(
                    f"Неизвестная зависимость {target!r} у {name}."
                )
    return graph


def valid_name(name):
    """Проверить имя пакета тестового репозитория."""
    return isinstance(name, str) and re.fullmatch(r"[A-Z]+", name) is not None


def traverse(root, neighbors, excluded):
    """Вернуть граф, порядок завершения DFS и рёбра, замыкающие циклы."""
    if excluded(root):
        return {}, [], []
    graph = {}
    finished = []
    active = {root}
    cycles = []
    stack = [(root, iter(expand(root, neighbors, excluded, graph)))]

    while stack:
        node, edges = stack[-1]
        target = next(edges, None)
        if target is None:
            stack.pop()
            active.remove(node)
            finished.append(node)
        elif target in active:
            cycles.append((node, target))
        elif target not in graph:
            active.add(target)
            stack.append(
                (target, iter(expand(target, neighbors, excluded, graph)))
            )
    return graph, finished, cycles


def expand(node, neighbors, excluded, graph):
    """Получить уникальные рёбра и занести узел в граф."""
    edges = list(dict.fromkeys(
        target for target in neighbors(node) if not excluded(target)
    ))
    graph[node] = edges
    return edges


"""Проверки обхода и локального источника."""

import unittest
from pathlib import Path

from src.graph import read_test_graph, traverse

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class GraphTests(unittest.TestCase):
    """Проверки графа на тестовом репозитории."""

    def test_shared_dependency(self):
        """Общая зависимость присутствует один раз, оба ребра сохранены."""
        source = read_test_graph(FIXTURES / "diamond.json")
        graph, finished, cycles = traverse("A", source.__getitem__, bool_false)
        self.assertEqual(graph, source)
        self.assertEqual(finished, ["D", "B", "C", "A"])
        self.assertEqual(cycles, [])

    def test_cycle(self):
        """Цикл сохраняется в графе, а обход заканчивается."""
        source = read_test_graph(FIXTURES / "cycle.json")
        graph, _, cycles = traverse("A", source.__getitem__, bool_false)
        self.assertEqual(graph, source)
        self.assertEqual(cycles, [("C", "A")])

    def test_filter(self):
        """Фильтр исключает узел, ребро и недостижимую ветвь."""
        source = read_test_graph(FIXTURES / "diamond.json")
        graph, _, _ = traverse("A", source.__getitem__, "B".__eq__)
        self.assertEqual(graph, {"A": ["C"], "C": ["D"], "D": []})


def bool_false(_node):
    """Разрешить все узлы."""
    return False


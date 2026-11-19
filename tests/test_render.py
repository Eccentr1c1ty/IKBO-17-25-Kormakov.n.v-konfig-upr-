"""Проверки текстового представления диаграммы."""

import unittest

from src.render import to_mermaid


class MermaidTests(unittest.TestCase):
    """Проверки сохранения структуры графа в тексте Mermaid."""

    def test_cycle_and_isolated_node(self):
        """Сохранить оба ребра цикла и отдельно стоящую вершину."""
        diagram = to_mermaid({"A": ["B"], "B": ["A"], "C": []})
        self.assertEqual(diagram.splitlines(), [
            "flowchart TD",
            '    p0["A"]',
            '    p1["B"]',
            '    p2["C"]',
            "    p0 --> p1",
            "    p1 --> p0",
        ])

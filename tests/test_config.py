import unittest

from src.main import validate_config


class ConfigTests(unittest.TestCase):
    """Проверки настроек первого этапа."""

    def setUp(self):
        self.config = {
            "package": "junit:junit",
            "repository": "https://repo.maven.apache.org/maven2/",
            "test_mode": False,
            "version": "4.13.2",
            "output_file": "dependencies.png",
            "filter_substring": "",
        }

    def test_valid_config(self):
        """Корректные настройки проходят проверку."""
        validate_config(self.config)

    def test_invalid_values(self):
        """Для каждого неверного значения ошибка называет нужное поле."""
        invalid_values = {
            "package": "junit",
            "repository": "abc",
            "test_mode": "false",
            "version": "",
            "output_file": "dependencies.txt",
            "filter_substring": 123,
        }

        for field, value in invalid_values.items():
            with self.subTest(field=field):
                config = {**self.config, field: value}
                with self.assertRaisesRegex(ValueError, rf"^{field}:"):
                    validate_config(config)
                print(f"{field}: ошибка обнаружена")
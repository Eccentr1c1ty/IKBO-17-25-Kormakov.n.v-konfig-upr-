# Визуализатор зависимостей Maven

Практическая работа по конфигурационному управлению, вариант № 9.

Программа строит транзитивный граф итеративным DFS. Для Maven загружает POM выбранной версии и обходит зависимости compile и runtime.

## Настройки

| Поле | Назначение |
| --- | --- |
| `package` | Координаты Maven `groupId:artifactId` или имя тестового пакета заглавными латинскими буквами |
| `repository` | URL Maven-репозитория или путь к тестовому файлу |
| `test_mode` | `true` для тестового файла, `false` для Maven-репозитория |
| `version` | Версия пакета |
| `output_file` | Имя выходного PNG-файла |
| `filter_substring` | Подстрока для фильтрации. Пустая строка отключает фильтр |

## Сборка, запуск и тесты

Сборка не требуется. Запуск из PowerShell в папке проекта:

```powershell
.\run.bat
```

Тесты через `uv`:

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" run --no-project --python 3.15 -m unittest discover -s tests -v
```

## Демонстрация обхода

Запуск без аргументов использует config.json и показывает граф JUnit.
Тестовый репозиторий — JSON-объект, где каждому имени пакета из
заглавных латинских букв соответствует список имён его зависимостей.

```powershell
.\run.bat tests\fixtures\diamond.config.json
.\run.bat tests\fixtures\cycle.config.json
.\run.bat tests\fixtures\filtered.config.json
```

Первый пример сохраняет два ребра к общей зависимости D, второй
показывает замыкающее ребро C → A, третий исключает пакет B по фильтру.

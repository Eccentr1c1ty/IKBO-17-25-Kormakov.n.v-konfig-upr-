# Визуализатор зависимостей Maven

Практическая работа по конфигурационному управлению, вариант № 9.

Утилита читает POM-файлы из Maven-репозитория, строит транзитивный
граф итеративным DFS и сохраняет его как текст Mermaid и изображение PNG.
Для проверки алгоритма также поддерживаются локальные тестовые графы.

## Настройки

| Поле | Назначение |
| --- | --- |
| `package` | Координаты Maven `groupId:artifactId` или имя тестового пакета заглавными латинскими буквами |
| `repository` | URL Maven-репозитория или путь к тестовому JSON-файлу. Относительный путь отсчитывается от папки проекта |
| `test_mode` | `true` для тестового файла, `false` для Maven-репозитория |
| `version` | Версия Maven-пакета. В тестовом режиме достаточно указать `"1"` |
| `output_file` | Имя PNG-файла в папке `output/`. Рядом сохраняется одноимённый файл `.mmd` |
| `filter_substring` | Подстрока для исключения по имени пакета. Регистр учитывается, пустая строка отключает фильтр |

Конфиг по умолчанию — `config.json`. Другой JSON-файл можно передать
первым аргументом. Если корень совпал с фильтром, граф будет пустым.

## Сборка, запуск и тесты

Сборка Python-кода не требуется. Для запуска нужен Python 3.12 или новее.
Для PNG нужен Mermaid CLI и доступный браузер. На другом компьютере
можно установить Mermaid CLI и проверить, что команда `mmdc --version`
доступна из терминала:

```powershell
npm install -g @mermaid-js/mermaid-cli@11.12.0
mmdc --version
```

В текущей Windows-настройке рендерер использует локально установленный
Mermaid CLI и Microsoft Edge. Конфигурация находится в
`%LOCALAPPDATA%\MavenVisualizerTools`.

Команды из корня проекта:

```powershell
.\run.bat
python -m unittest discover -s tests -v
```

Если Python установлен через `uv`, запуск тестов из PowerShell:

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" run --no-project --python 3.15 -m unittest discover -s tests -v
```

## Тестовый граф

Тестовый репозиторий — JSON-объект. Ключи задают имена пакетов,
а значения перечисляют их прямые зависимости. Например:

```json
{"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
```

```powershell
.\run.bat tests\fixtures\diamond.config.json
.\run.bat tests\fixtures\cycle.config.json
.\run.bat tests\fixtures\filtered.config.json
```

В первом примере сохраняются оба ребра к D. Во втором сохраняется
замыкающее ребро C → A и выводится сообщение о цикле. В третьем
граф исключает B, но сохраняет путь A → C → D.

## Порядок загрузки в коммите этапа 4

В ациклическом графе программа выводит вершины в порядке завершения DFS:
зависимость появляется раньше использующего её пакета. Корневой пакет
появляется последним. Для цикла программа выводит причину и код ошибки 1.

| Конфигурация | Результат |
| --- | --- |
| diamond | D, B, C, A |
| filtered | D, C, A |
| cycle | Порядок невозможен, ребро C → A замыкает цикл |

Для сравнения запущен Maven 3.9.11 на проекте с единственной прямой
зависимостью junit:junit:4.13.2. Команда:

```powershell
mvn -B "-Dmaven.repo.local=<пустой локальный репозиторий>" org.apache.maven.plugins:maven-dependency-plugin:3.8.1:resolve
```

В журнале строка «Downloading» для junit-4.13.2.jar стояла перед строкой
для hamcrest-core-1.3.jar. Утилита выводит сначала Hamcrest, затем JUnit.
DFS вычисляет порядок зависимостей в графе. Maven разрешает метаданные
и может запрашивать JAR независимо от такого порядка. Запись
«Downloading» показывает начало запроса. При повторном запуске кэш
Maven может убрать эти строки.


## Визуализация трёх Maven-пакетов

```powershell
.\run.bat
.\run.bat examples\commons-beanutils.json
.\run.bat examples\commons-csv.json
```

| Пакет | Текст Mermaid | Изображение |
| --- | --- | --- |
| JUnit 4.13.2 | `output/junit.mmd` | `output/junit.png` |
| Commons BeanUtils 1.9.4 | `output/commons-beanutils.mmd` | `output/commons-beanutils.png` |
| Commons CSV 1.10.0 | `output/commons-csv.mmd` | `output/commons-csv.png` |

Для каждого пакета проверен вывод Maven 3.9.11. В чистом Maven-проекте
указывалась одна зависимость с соответствующими координатами и версией.
Команда была одинаковой для всех трёх примеров:

```powershell
mvn -B org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree
```

| Пакет | Сравнение с Maven после исключения корня контрольного проекта |
| --- | --- |
| JUnit | В обоих графах JUnit → Hamcrest Core 1.3. Объявление Hamcrest Library с областью test не попадает в граф compile/runtime. |
| Commons BeanUtils | Оба графа содержат прямые зависимости Commons Logging 1.2 и Commons Collections 3.2.2. Утилита дополнительно рисует ветви Log4j, LogKit и Avalon Framework. Они помечены как optional в POM Commons Logging и поэтому отсутствуют в транзитивном дереве Maven. |
| Commons CSV | В обоих графах только выбранный пакет. Зависимостей compile/runtime у него нет. |

Утилита читает верхнеуровневые объявления `compile`/`runtime` в POM
и подставляет свойства из этого же POM. Такой обход сохраняет
объявленные optional-ветви. Родительские POM, BOM, профили,
`exclusions` и разрешение конфликтов версий Maven не реализованы.

## История этапов

В Git сохранены отдельные версии с выводом настроек, прямых
зависимостей, графа, порядка загрузки и визуализацией соответственно.
Текущая версия выводит граф и пути к Mermaid и PNG.


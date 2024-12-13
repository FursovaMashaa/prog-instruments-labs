import csv
import hashlib
import json
import re

from json import load
from typing import Dict, List, Optional
from path import CSV_PATH, JSON_PATH, PATH_TO_PATERNS

def read_csv(file_path: str) -> Optional[list[list[str]]]:
    """
    Читает данные из CSV-файла, который имеет разделитель ';'.

    :param file_path (str): Путь к CSV-файлу.
    :return Optional[list[list[str]]]: Двумерный список строк, представляющий данные из файла,
                                    или None, если файл не может быть прочитан.
    """
    data=[]
    with open(file_path, mode="r", encoding='utf-16') as csvfile:
        for_help = csv.reader(csvfile, delimiter=';')
        for row in for_help:
            data.append(row)
        return data

def read_json(file_path: str) -> Optional[dict]:
    """
    Читает данные из JSON-файла.

    :param file_path (str): Путь к JSON-файлу.
    :return Optional[dict]: Словарь, представляющий данные из файла,
                        или None, если файл не может быть прочитан.
    """
    with open(file_path, "r", encoding="UTF-8") as file:
        return load(file)


def validate_row(row: list[str], patterns: dict[str, str]) -> bool:
    """Проверяет, соответствуют ли все значения в строке заданным шаблонам.

    Эта функция проверяет каждую строку данных на соответствие регулярным выражениям,
    указанным в словаре 'patterns'. Если хотя бы одно значение не соответствует своему шаблону,
    возвращается False.

    :param row: Список строковых значений, представляющих одну строку данных.
    :param patterns: Словарь, содержащий имена столбцов и соответствующие им регулярные выражения.
    :return: True, если все значения в строке соответствуют своим шаблонам, иначе False.
    """
    for val, pattern in zip(row, patterns.values()):
        if not re.match(pattern, val):
            return False
    return True


def find_invalid_data(patterns: Dict[str, str], data: list) -> list[int]:
    """Ищет индексы строк с неверными данными.

    Эта функция проходит через весь набор данных и находит строки, содержащие значения,
    которые не соответствуют шаблонам, указанным в словаре 'patterns'.

    :param patterns: Словарь, содержащий имена столбцов и соответствующие им регулярные выражения.
    :param data: Список списков строковых значений, представляющий набор данных.
    :return: Список индексов строк с неверными данными.
    """
    invalid_indices = []
    for index, row in enumerate(data[1:]):
        if not validate_row(row, patterns):
            invalid_indices.append(index)
    return invalid_indices

def calculate_checksum(row_numbers: List[int]) -> str:
    """
    Вычисляет md5 хеш от списка целочисленных значений.

    ВНИМАНИЕ, ВАЖНО! Чтобы сумма получилась корректной, считать, что первая строка с данными csv-файла имеет номер 0
    Другими словами: В исходном csv 1я строка - заголовки столбцов, 2я и остальные - данные.
    Соответственно, считаем что у 2 строки файла номер 0, у 3й - номер 1 и так далее.

    Надеюсь, я расписал это максимально подробно.
    Хотя что-то мне подсказывает, что обязательно найдется человек, у которого с этим возникнут проблемы.
    Которому я отвечу, что все написано в докстринге ¯\_(ツ)_/¯

    :param row_numbers: список целочисленных номеров строк csv-файла, на которых были найдены ошибки валидации
    :return: md5 хеш для проверки через github action
    """
    row_numbers.sort()
    return hashlib.md5(json.dumps(row_numbers).encode('utf-8')).hexdigest()

def serialize_result(variant: int, checksum: str) -> None:
    """
    Метод для сериализации результатов лабораторной пишите сами.
    Вам нужно заполнить данными - номером варианта и контрольной суммой - файл, лежащий в папке с лабораторной.
    Файл называется, очевидно, result.json.

    ВНИМАНИЕ, ВАЖНО! На json натравлен github action, который проверяет корректность выполнения лабораторной.
    Так что не перемещайте, не переименовывайте и не изменяйте его структуру, если планируете успешно сдать лабу.

    :param variant: номер вашего варианта
    :param checksum: контрольная сумма, вычисленная через calculate_checksum()
    """
    result = {
        "variant": variant,
        "checksum": checksum
    }
    with open("result.json", mode="w", encoding="utf-8") as f:
        json.dump(result, f)

if __name__ == "__main__":
    var=28
    pattern = read_json(PATH_TO_PATERNS)
    data = read_csv(CSV_PATH)
    invalid = find_invalid_data(pattern, data)
    check_sum = calculate_checksum(invalid)
    print(check_sum)
    serialize_result(var, check_sum)

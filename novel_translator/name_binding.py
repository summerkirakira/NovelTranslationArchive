import csv
from io import StringIO
from pathlib import Path


def csv_text_to_dict(csv_text: str):
    f = StringIO(csv_text)
    reader = csv.DictReader(f)
    data = [row for row in reader]
    return data


def dict_to_csv_text(data: list):
    if len(data) == 0:
        return ''
    f = StringIO()
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return f.getvalue()


def remove_duplicate(data: list, key: str):
    return list({v[key]: v for v in data}.values())


def load_name_binding_list(file: Path):
    if not file.exists():
        return []
    with open(file, 'r') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    return data


def save_name_binding_list(file: Path, data: list):
    with open(file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':
    csv_text = """姓名,年龄,城市
    张三,25,北京
    李四,30,上海
    王五,28,广州"""
    a = csv_text_to_dict(csv_text)
    print(a)

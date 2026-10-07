import pytest

from app.data.data_reader import DataError, extract_names, load_data


def test_load_names_valid(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name\nAlice\nBob\n  Charlie  \n", encoding="utf-8")
    _, rows = load_data(csv_file)
    names, duplicates = extract_names(rows, "Name")
    assert names == ["Alice", "Bob", "Charlie"]
    assert duplicates == 0


def test_load_names_case_insensitive_header(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name\nAlice\n", encoding="utf-8")
    _, rows = load_data(csv_file)
    names, _ = extract_names(rows, "Name")
    assert names == ["Alice"]


def test_load_names_with_bom(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name\nAlice\n", encoding="utf-8-sig")
    _, rows = load_data(csv_file)
    names, _ = extract_names(rows, "Name")
    assert names == ["Alice"]


def test_load_names_missing_column(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Age,City\n25,NY\n", encoding="utf-8")
    _, rows = load_data(csv_file)
    with pytest.raises(
        DataError, match="No participant names were found in column 'Name'"
    ):
        extract_names(rows, "Name")


def test_load_names_empty_rows(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name\nAlice\n\n  \nBob", encoding="utf-8")
    _, rows = load_data(csv_file)
    names, _ = extract_names(rows, "Name")
    assert names == ["Alice", "Bob"]


def test_load_names_duplicates(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name\nAlice\nBob\nAlice\n", encoding="utf-8")
    _, rows = load_data(csv_file)
    names, duplicates = extract_names(rows, "Name")
    assert names == ["Alice", "Bob", "Alice"]
    assert duplicates == 1


def test_load_data_trailing_ghost_columns(tmp_path):
    csv_file = tmp_path / "ghost.csv"
    # 2 real columns and 5 trailing empty comma columns
    csv_file.write_text(
        "ID,Name,,,,,\n101,Alice,,,,,\n102,Bob,,,,,\n,,,,,\n",
        encoding="utf-8",
    )
    headers, rows = load_data(csv_file)
    assert headers == ["ID", "Name"]
    assert len(rows) == 2
    assert rows[0] == {"ID": "101", "Name": "Alice"}
    assert rows[1] == {"ID": "102", "Name": "Bob"}


import csv
from pathlib import Path


class DataError(Exception):
    pass


def load_data(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """
    Load headers and rows from CSV or Excel.
    Returns (headers, list_of_dicts).
    """
    ext = file_path.suffix.lower()
    if ext == ".csv":
        return _load_csv(file_path)
    elif ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
        return _load_excel(file_path)
    else:
        raise DataError("Unsupported file format. Please upload CSV or Excel.")


def _load_csv(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
            return _parse_csv(f)
    except UnicodeDecodeError:
        try:
            with open(csv_path, mode="r", encoding="latin-1", newline="") as f:
                return _parse_csv(f)
        except Exception as e:
            raise DataError("Unable to read the CSV file.") from e
    except Exception as e:
        raise DataError("Unable to read the CSV file.") from e


def _parse_csv(file_obj) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.reader(file_obj)
    try:
        headers = next(reader)
    except StopIteration:
        raise DataError("The file is empty.")

    headers = [str(h).strip() for h in headers]
    if not headers:
        raise DataError("No headers found in the file.")

    rows = []
    for row in reader:
        row_dict = {}
        for i, h in enumerate(headers):
            val = row[i].strip() if i < len(row) else ""
            row_dict[h] = val
        rows.append(row_dict)

    return headers, rows


def _load_excel(excel_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
        sheet = wb.active

        headers = []
        rows = []

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                headers = [
                    str(cell).strip() if cell is not None else f"Column_{j+1}"
                    for j, cell in enumerate(row)
                ]
                if not headers:
                    raise DataError("No headers found in the Excel file.")
            else:
                row_dict = {}
                for j, h in enumerate(headers):
                    val = (
                        str(row[j]).strip()
                        if j < len(row) and row[j] is not None
                        else ""
                    )
                    row_dict[h] = val
                rows.append(row_dict)

        wb.close()
        return headers, rows
    except Exception as e:  # noqa: BLE001
        raise DataError(f"Unable to read the Excel file: {e!s}")


def extract_names(
    rows: list[dict[str, str]], column_name: str
) -> tuple[list[str], int]:
    names = []
    seen = set()
    duplicates = 0

    for row in rows:
        name = row.get(column_name, "").strip()
        if name:
            if name in seen:
                duplicates += 1
            seen.add(name)
            names.append(name)

    if not names:
        raise DataError(f"No participant names were found in column '{column_name}'.")

    return names, duplicates

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
    reader = list(csv.reader(file_obj))
    if not reader:
        raise DataError("The file is empty.")

    # Find header row (first non-empty row)
    header_row = None
    data_rows = []
    for row in reader:
        if not row or all(str(cell).strip() == "" for cell in row):
            continue
        if header_row is None:
            header_row = row
        else:
            data_rows.append(row)

    if header_row is None:
        raise DataError("No headers found in the file.")

    col_count = len(header_row)
    valid_col_indices = []
    for col_idx in range(col_count):
        h_str = header_row[col_idx].strip() if col_idx < len(header_row) else ""
        has_data = any(
            col_idx < len(r) and str(r[col_idx]).strip() != ""
            for r in data_rows
        )
        if h_str or has_data:
            valid_col_indices.append(col_idx)

    if not valid_col_indices:
        raise DataError("No valid columns found in the CSV file.")

    headers = []
    for col_idx in valid_col_indices:
        h_str = header_row[col_idx].strip() if col_idx < len(header_row) else ""
        if not h_str:
            h_str = f"Column_{col_idx + 1}"
        unique_h = h_str
        counter = 2
        while unique_h in headers:
            unique_h = f"{h_str}_{counter}"
            counter += 1
        headers.append(unique_h)

    rows = []
    for r in data_rows:
        if all(
            col_idx >= len(r) or str(r[col_idx]).strip() == ""
            for col_idx in valid_col_indices
        ):
            continue  # skip completely blank row

        row_dict = {}
        for h, col_idx in zip(headers, valid_col_indices):
            val = r[col_idx].strip() if col_idx < len(r) else ""
            row_dict[h] = val
        rows.append(row_dict)

    if not rows:
        raise DataError("No data records found in the file.")

    return headers, rows


def _load_excel(excel_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
        sheet = wb.active

        raw_rows = list(sheet.iter_rows(values_only=True))
        wb.close()

        if not raw_rows:
            raise DataError("The Excel file is empty.")

        # Find header row (first non-empty row)
        header_row = None
        data_rows = []
        for row in raw_rows:
            if not row or all(
                cell is None or str(cell).strip() == "" for cell in row
            ):
                continue
            if header_row is None:
                header_row = row
            else:
                data_rows.append(row)

        if header_row is None:
            raise DataError("No data found in the Excel file.")

        col_count = len(header_row)
        valid_col_indices = []
        for col_idx in range(col_count):
            h_val = header_row[col_idx]
            h_str = str(h_val).strip() if h_val is not None else ""
            has_data = any(
                col_idx < len(r)
                and r[col_idx] is not None
                and str(r[col_idx]).strip() != ""
                for r in data_rows
            )
            if h_str or has_data:
                valid_col_indices.append(col_idx)

        if not valid_col_indices:
            raise DataError("No valid columns found in the Excel file.")

        headers = []
        for col_idx in valid_col_indices:
            h_val = header_row[col_idx]
            h_str = str(h_val).strip() if h_val is not None else ""
            if not h_str:
                h_str = f"Column_{col_idx + 1}"
            unique_h = h_str
            counter = 2
            while unique_h in headers:
                unique_h = f"{h_str}_{counter}"
                counter += 1
            headers.append(unique_h)

        rows = []
        for r in data_rows:
            if all(
                col_idx >= len(r)
                or r[col_idx] is None
                or str(r[col_idx]).strip() == ""
                for col_idx in valid_col_indices
            ):
                continue  # skip completely blank row

            row_dict = {}
            for h, col_idx in zip(headers, valid_col_indices):
                val = ""
                if col_idx < len(r) and r[col_idx] is not None:
                    val = str(r[col_idx]).strip()
                row_dict[h] = val
            rows.append(row_dict)

        if not rows:
            raise DataError("No data records found in the Excel file.")

        return headers, rows
    except DataError:
        raise
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
            name = name.title()
            if name in seen:
                duplicates += 1
            seen.add(name)
            names.append(name)

    if not names:
        raise DataError(f"No participant names were found in column '{column_name}'.")

    return names, duplicates


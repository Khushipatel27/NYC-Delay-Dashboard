# core_data.py
from typing import List, Dict, Any, Callable
# Helper Functions
def _normalize_day_type(value):
    """Normalize day_type values:
       1 → Weekday
       2 → Weekend
       '1' → Weekday
       '2' → Weekend
       Already-clean strings remain unchanged.
    """
    if isinstance(value, int):
        return "Weekday" if value == 1 else "Weekend" if value == 2 else value

    if isinstance(value, str):
        s = value.strip()
        if s in ("1", "2"):
            return "Weekday" if s == "1" else "Weekend"
        if s.lower() == "weekday":
            return "Weekday"
        if s.lower() == "weekend":
            return "Weekend"
        return value

    return value


def _to_int_or_none(value):
    """Convert values to int, or None if conversion fails."""
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except Exception:
        return None
# CSV Parser
class CSVParser:
    """
    Reads CSV data, correctly handling fields enclosed in double quotes
    that contain the separator (commas).
    """

    def __init__(self, file_name: str, separator: str = ",") -> None:
        self.file_name = file_name
        self.separator = separator
        self.columns: List[str] = []
        self.data: List[List[str]] = []

    def _parse_line(self, line: str) -> List[str]:
        """Custom parser for a single CSV line."""
        fields = []
        current_field = ""
        in_quotes = False

        # Add sentinel separator at end to simplify logic
        line_with_sentinel = line.strip() + self.separator

        for char in line_with_sentinel:
            if char == '"':
                in_quotes = not in_quotes
            elif char == self.separator and not in_quotes:
                fields.append(current_field.strip().strip('"'))
                current_field = ""
            else:
                current_field += char

        # Sometimes last sentinel produces empty field → remove
        if fields and fields[-1] == "":
            fields.pop()

        return fields

    def read_csv(self) -> bool:
        """Reads CSV file, sets self.columns and self.data."""
        self.data.clear()
        self.columns.clear()

        try:
            with open(self.file_name, "r") as f:
                header_line = f.readline().strip()
                if not header_line:
                    print("Error: CSV file is empty.")
                    return False

                # Standardize headers (all lowercase)
                self.columns = [
                    col.strip().lower()
                    for col in header_line.split(self.separator)
                ]

                rows_skipped = 0

                for line in f:
                    if line.strip():
                        row = self._parse_line(line)
                        if len(row) == len(self.columns):
                            self.data.append(row)
                        else:
                            rows_skipped += 1

                if rows_skipped > 0:
                    print(f"Warning: Skipped {rows_skipped} malformed rows.")

            print(f"Successfully loaded {len(self.data)} rows from {self.file_name}")
            return True

        except Exception as e:
            print(f"An error occurred during parsing: {e}")
            return False

# DataFrame Class
class DataFrame:
    """A custom DataFrame with select, filter, group_by, and join."""
    def __init__(self, data_rows: List[List[str]], columns: List[str]):
        self.columns = columns
        self.df_dict: Dict[str, List[Any]] = {col: [] for col in columns}

        # Fill columns with conversion
        for row in data_rows:
            for i, value in enumerate(row):
                col = columns[i]

                if col == "delays":
                    value = _to_int_or_none(value)
                elif col == "day_type":
                    value = _normalize_day_type(value)

                self.df_dict[col].append(value)

        self._length = len(data_rows)

    
    # Utility methods
    def __len__(self):
        return self._length

    def to_rows(self, n: int = None) -> List[Dict[str, Any]]:
        """Return DataFrame as list of dict rows."""
        max_rows = self._length if n is None else min(n, self._length)
        rows = []
        for i in range(max_rows):
            rows.append({col: self.df_dict[col][i] for col in self.columns})
        return rows

    def head(self, n: int):
        """Return first n rows as new DataFrame."""
        subset_rows = [
            [self.df_dict[col][i] for col in self.columns]
            for i in range(min(n, self._length))
        ]
        return DataFrame(subset_rows, self.columns)

    
    # Relational operations
    def select(self, cols: List[str]):
        """Projection."""
        cols = [c.lower() for c in cols]
        new_cols = [c for c in cols if c in self.columns]

        new_data = []
        for i in range(self._length):
            row = [self.df_dict[col][i] for col in new_cols]
            new_data.append(row)

        return DataFrame(new_data, new_cols)

    def filter_data(self, condition: Callable[[int, Dict[str, List[Any]]], bool]):
        """Row filtering (like SQL WHERE)."""
        filtered = []
        for i in range(self._length):
            if condition(i, self.df_dict):
                filtered.append([self.df_dict[col][i] for col in self.columns])
        return DataFrame(filtered, self.columns)

    def group_by(
        self,
        group_cols: List[str],
        agg_col: str,
        agg_func: str = "sum",
        new_col_name: str = None,):
          
        """Group and aggregate (sum, count, max, min, avg)."""
        group_cols = [c.lower() for c in group_cols]
        agg_col = agg_col.lower()

        if new_col_name is None:
            new_col_name = f"{agg_func}_{agg_col}"

        # For AVG, we keep sum + count separately
        groups = {}   # key → aggregate (or sum)
        counts = {}   # key → count (for avg only)

        for i in range(self._length):
            key = tuple(self.df_dict[col][i] for col in group_cols)
            val = self.df_dict[agg_col][i]

            # Skip None for numeric aggregations
            if val is None and agg_func in ("sum", "max", "min", "avg"):
                continue

            # FIRST TIME we see this key
            if key not in groups:
                if agg_func == "sum":
                    groups[key] = val
                elif agg_func == "count":
                    groups[key] = 1
                elif agg_func in ("max", "min"):
                    groups[key] = val
                elif agg_func == "avg":
                    groups[key] = val     # start sum
                    counts[key] = 1       # start count
                else:
                    raise ValueError("Unsupported aggregation")

            # LATER rows for the same key
            else:
                if agg_func == "sum":
                    groups[key] += val
                elif agg_func == "count":
                    groups[key] += 1
                elif agg_func == "max":
                    if val > groups[key]:
                        groups[key] = val
                elif agg_func == "min":
                    if val < groups[key]:
                        groups[key] = val
                elif agg_func == "avg":
                    groups[key] += val      # accumulate sum
                    counts[key] += 1        # accumulate count

        # Build the output rows
        new_rows = []
        for key in groups:
            if agg_func == "avg":
                agg_val = groups[key] / counts[key] if counts[key] > 0 else None
            else:
                agg_val = groups[key]

            new_rows.append(list(key) + [agg_val])

        new_columns = group_cols + [new_col_name]
        return DataFrame(new_rows, new_columns)

    # Join operation
    def join(self, other, left_on, right_on, how="inner"):
        """
        Custom join implementation (supports INNER and LEFT).
        left_on: column in self
        right_on: column in other
        how: 'inner' or 'left'
        """
        left_on = left_on.lower()
        right_on = right_on.lower()

        if left_on not in self.columns:
            raise ValueError(f"Column {left_on} not found in left table")

        if right_on not in other.columns:
            raise ValueError(f"Column {right_on} not found in right table")

        result_cols = [f"left_{c}" for c in self.columns] + \
                      [f"right_{c}" for c in other.columns]

        result_rows = []

        # Build index for other (right table)
        index = {}
        for j in range(len(other)):
            key = other.df_dict[right_on][j]
            index.setdefault(key, []).append(j)

        # Perform join
        for i in range(len(self)):
            left_value = self.df_dict[left_on][i]

            if left_value in index:
                # matched rows exist
                for j in index[left_value]:
                    row = []
                    # left table values
                    for c in self.columns:
                        row.append(self.df_dict[c][i])
                    # right table values
                    for c in other.columns:
                        row.append(other.df_dict[c][j])
                    result_rows.append(row)
            else:
                # no match → LEFT join keeps row with NULLs
                if how == "left":
                    row = []
                    for c in self.columns:
                        row.append(self.df_dict[c][i])
                    for c in other.columns:
                        row.append(None)
                    result_rows.append(row)

        return DataFrame(result_rows, result_cols)

# Pretty Table Printer (for debugging)
def print_table(df: DataFrame, n: int = 10) -> None:
    """Simple console printer for debugging / notebook use."""
    rows = df.to_rows(n)
    if not rows:
        print("(no rows)")
        return

    cols = df.columns
    widths = {c: len(c) for c in cols}
    for r in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(r[c])))

    header = " | ".join(f"{c.upper():<{widths[c]}}" for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    print(header)
    print(sep)
    for r in rows:
        line = " | ".join(f"{str(r[c]):<{widths[c]}}" for c in cols)
        print(line)

# Convenience loader for the project
def load_mta_data(csv_path: str) -> DataFrame:
    """
    Load a CSV using CSVParser and return it as a custom DataFrame.
    """
    parser = CSVParser(csv_path)
    ok = parser.read_csv()
    if not ok:
        raise RuntimeError("CSV loading failed")
    return DataFrame(parser.data, parser.columns)

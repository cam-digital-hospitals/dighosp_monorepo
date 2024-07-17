"""Functions for reading Excel data.

Note that to obtain computed values, workbooks should be loaded with `data_only=True`.
"""

import openpyxl as oxl
from openpyxl.cell.cell import Cell


def get_name(wbook: oxl.Workbook, name: str):
    """Read an Excel named range. If the range refers to a single cell,
    return that cell's value; else, return the range's cell values as a list of lists."""
    worksheet, cell_range = list(wbook.defined_names[name].destinations)[0]
    # strip $ from cell range string
    cell_range = str.replace(cell_range, '$', '')
    cells = wbook[worksheet][cell_range]
    if isinstance(cells, Cell):
        return cells.value
    return [[cell.value for cell in row] for row in cells]


def get_table(wbook: oxl.Workbook, sheet_name: str, name: str):
    """Read an Excel table and convert to a list of lists."""
    worksheet = wbook[sheet_name]
    cell_range = worksheet[worksheet.tables[name].ref]
    return [[cell.value for cell in r] for r in cell_range]

import csv
from pathlib import Path


DATA_DIR = Path(__file__).parent
SOURCE = DATA_DIR / "retail_sales_dirty.csv"
WORKING = DATA_DIR / "retail_sales_working.csv"
QUALITY_LOG = DATA_DIR / "data_quality_log.csv"


def main():
    with SOURCE.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        fieldnames = reader.fieldnames
        source_rows = list(reader)

    working_rows = []
    quality_log = []
    seen_rows = set()

    for source_line, row in enumerate(source_rows, start=2):
        original = dict(row)
        row = {key: value.strip() for key, value in row.items()}

        if row["Region"].casefold() == "south":
            if row["Region"] != "South":
                quality_log.append({
                    "issue_type": "Category consistency",
                    "field_row": f"Region, row {source_line}",
                    "evidence": original["Region"],
                    "decision": "Standardized to South",
                    "reason": "Case and surrounding spaces represented the same region.",
                })
            row["Region"] = "South"

        if row["Category"] == "Electronic":
            quality_log.append({
                "issue_type": "Category consistency",
                "field_row": f"Category, row {source_line}",
                "evidence": original["Category"],
                "decision": "Standardized to Electronics",
                "reason": "Product P-A is consistently categorized as Home elsewhere.",
            })
            row["Category"] = "Home"

        row_key = tuple(row[field] for field in fieldnames)
        if row_key in seen_rows:
            quality_log.append({
                "issue_type": "Duplicate",
                "field_row": f"row {source_line}",
                "evidence": "Exact duplicate of an earlier row",
                "decision": "Removed from working copy",
                "reason": "The duplicate has identical values in every field.",
            })
            continue
        seen_rows.add(row_key)

        if not row["Sales"]:
            quality_log.append({
                "issue_type": "Missing value",
                "field_row": f"Sales, row {source_line}",
                "evidence": "blank",
                "decision": "Flagged; not imputed",
                "reason": "Sales cannot be derived defensibly from the available fields.",
            })
        if not row["Profit"]:
            quality_log.append({
                "issue_type": "Missing value",
                "field_row": f"Profit, row {source_line}",
                "evidence": "blank",
                "decision": "Flagged; not imputed",
                "reason": "Profit is not filled without an approved imputation rule.",
            })
        if row["Discount"] == "2.5":
            quality_log.append({
                "issue_type": "Impossible value",
                "field_row": f"Discount, row {source_line}",
                "evidence": "2.5",
                "decision": "Flagged; not changed",
                "reason": "The intended correction (for example 0.25) is not confirmed.",
            })
        if row["Quantity"] == "-2":
            quality_log.append({
                "issue_type": "Impossible value",
                "field_row": f"Quantity, row {source_line}",
                "evidence": "-2",
                "decision": "Flagged; not changed",
                "reason": "It may represent a return, but no return rule is defined.",
            })

        working_rows.append(row)

    with WORKING.open("w", newline="", encoding="utf-8") as working_file:
        writer = csv.DictWriter(working_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(working_rows)

    log_fields = ["issue_type", "field_row", "evidence", "decision", "reason"]
    with QUALITY_LOG.open("w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=log_fields)
        writer.writeheader()
        writer.writerows(quality_log)

    print(f"Working rows: {len(working_rows)}")
    print(f"Quality-log entries: {len(quality_log)}")
    print(f"Created: {WORKING}")
    print(f"Created: {QUALITY_LOG}")


if __name__ == "__main__":
    main()
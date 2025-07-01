from sqlalchemy.orm import InstrumentedAttribute


def build_conditions(model, filters: dict):
    conditions = []

    for key, value in filters.items():
        if "__" in key:
            field_name, operator = key.split("__", 1)
        else:
            field_name, operator = key, "eq"

        column: InstrumentedAttribute = getattr(model, field_name)
        if column is None:
            continue

        if operator == "eq":
            conditions.append(column == value)
        elif operator == "icontains":
            conditions.append(column.ilike(f"%{value}%"))

    return conditions

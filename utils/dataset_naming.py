from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path


RAW_FILE_PREFIX = "raw_nasional_logistics_data"


def _as_batch_date(value: date | datetime | str | None = None) -> date:
    if value is None:
        return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def next_raw_batch_path(
    raw_dir: str | Path,
    processed_dir: str | Path,
    source_label: str | None = None,
    batch_date: date | datetime | str | None = None,
) -> Path:
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    batch_date_value = _as_batch_date(batch_date)
    date_token = batch_date_value.strftime("%Y%m%d")
    label_part = f"_{source_label.strip().lower()}" if source_label else ""
    pattern = re.compile(
        rf"^(?:done_)?{RAW_FILE_PREFIX}(?:_[a-z]+)?_{date_token}_batch(\d+)\.csv$"
    )

    last_batch = 0
    for directory in (raw_dir, processed_dir):
        if not directory.exists():
            continue
        for path in directory.glob(f"*{date_token}_batch*.csv"):
            match = pattern.match(path.name)
            if match:
                last_batch = max(last_batch, int(match.group(1)))

    next_batch = last_batch + 1
    filename = f"{RAW_FILE_PREFIX}{label_part}_{date_token}_batch{next_batch:03d}.csv"
    return raw_dir / filename

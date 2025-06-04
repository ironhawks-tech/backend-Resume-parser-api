from dateutil import parser
from datetime import datetime
import re
from typing import List, Tuple, Dict


def parse_duration_to_years(duration_text: str) -> float:
    """
    Given a string like “Jan 2023 – Jun 2023” or “July 2022 – Present”,
    return a float rounding to one decimal (e.g. 0.5 or 0.3).
    If parsing fails, returns 0.0.
    """
    try:
        parts = re.split(r"[-–—]+", duration_text)
        if len(parts) != 2:
            return 0.0

        start_str = parts[0].strip()
        end_str = parts[1].strip().lower()

        start_date = parser.parse(start_str, fuzzy=True)
        if "present" in end_str or "current" in end_str:
            end_date = datetime.today()
        else:
            end_date = parser.parse(end_str, fuzzy=True)

        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        years_float = round(total_months / 12, 1)
        return years_float
    except Exception:
        return 0.0


def compute_experience_list(raw_experience_list: List[Dict[str, str]]) -> Tuple[List[Dict[str, object]], float]:
    """
    Takes Mistral's raw list of experience entries (with "duration" strings),
    returns:
      • updated_experience: same list but each entry has "years": decimal
      • total_experience: float sum of all years
    """
    total_exp = 0.0
    updated = []

    for entry in raw_experience_list:
        duration_text = entry.get("duration", "")
        years = parse_duration_to_years(duration_text)
        total_exp += years

        updated.append({
            "job_title": entry.get("job_title", ""),
            "company": entry.get("company", ""),
            "years": years
        })

    return updated, round(total_exp, 1)

"""Anonymous usage statistics for the joint petition interview.

note_section() records, once per session, how many seconds after the start each
main section was reached, and keeps one statistics record per session current.
The record holds section names and times only: no names or other answers. The
interview stores the first spouse's ZIP code in the same record when it ends.
"""
from docassemble.base.util import (
    as_datetime,
    current_datetime,
    define,
    defined,
    store_variables_snapshot,
    value,
)

__all__ = ["note_section", "statistics_data"]

LOG = "al_section_log"


def _log():
    if defined(LOG):
        return value(LOG)
    return {"started": current_datetime().isoformat(), "reached": {}}


def statistics_data(**extra):
    """The statistics record: section times plus anything the caller adds."""
    log = _log()
    data = {"section_seconds": dict(log["reached"]), "last_section": log.get("last")}
    data.update(extra)
    return data


def note_section(section):
    """Record the first time the interview reaches a section. The interview's
    order code runs again on every screen, so later calls do nothing."""
    log = _log()
    if section in log["reached"]:
        return
    elapsed = (current_datetime() - as_datetime(log["started"])).total_seconds()
    log["reached"][section] = int(elapsed)
    log["last"] = section
    define(LOG, log)
    store_variables_snapshot(
        data=statistics_data(reached_interview_end=False),
        key="statistics",
        persistent=True,
    )

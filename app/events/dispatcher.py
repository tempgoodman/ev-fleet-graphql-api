def dispatch_ev_status_changed(ev_id: str, old_status: str, new_status: str) -> None:
    print(f"[EV_STATUS_CHANGED] EV {ev_id}: {old_status} -> {new_status}")

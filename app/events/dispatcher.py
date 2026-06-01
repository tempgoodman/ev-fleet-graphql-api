def dispatch_ev_status_changed(ev_id: str, old_status: str, new_status: str) -> None:
    # TODO: Replace this mock logger with a real RabbitMQ or AWS EventBridge/SNS publisher
    # to trigger downstream services (e.g., Billing and Logistics) asynchronously in production.
    print(f"[EV_STATUS_CHANGED] EV {ev_id}: {old_status} -> {new_status}")

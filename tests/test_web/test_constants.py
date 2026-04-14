from app.web.constants import AuditEvents


def test_audit_event_names_are_uppercase_strings():
    for name in [
        "ADMIN_LOGIN", "ADMIN_LOGIN_FAILED", "ADMIN_LOGOUT",
        "TICKET_STATUS_UPDATED", "TICKET_ASSIGNED", "TICKET_ESCALATION_UPDATED",
        "NOTIFICATION_SENT", "FILE_DOWNLOADED",
    ]:
        value = getattr(AuditEvents, name)
        assert isinstance(value, str) and value == name

from datetime import datetime, timedelta


def format_duration(minutes: int) -> str:
    if minutes is None:
        return "0:00"
    h = minutes // 60
    m = minutes % 60
    return f"{h}:{m:02d}"


def format_duration_from_seconds(seconds: float) -> str:
    minutes = int(seconds) // 60
    return format_duration(minutes)


def format_currency(amount: float) -> str:
    return f"{amount:.2f} ج.م"


def format_datetime(dt: datetime) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")


def format_date(dt: datetime) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d")


def format_time(dt: datetime) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%H:%M")


def get_session_duration_text(session) -> str:
    if session.end_time and session.start_time:
        diff = (session.end_time - session.start_time).total_seconds() / 60
        return format_duration(int(diff))
    elif session.start_time:
        diff = (datetime.now() - session.start_time).total_seconds() / 60
        return format_duration(int(diff))
    return "0:00"


def get_active_session_duration_minutes(session) -> int:
    if session.end_time and session.start_time:
        return int((session.end_time - session.start_time).total_seconds() / 60)
    elif session.start_time:
        return int((datetime.now() - session.start_time).total_seconds() / 60)
    return 0


STATUS_COLORS = {
    "available": "#22c55e",
    "occupied": "#ef4444",
    "maintenance": "#f59e0b",
    "reserved": "#3b82f6",
    "active": "#22c55e",
    "completed": "#6b7280",
    "cancelled": "#ef4444",
    "pending": "#f59e0b",
    "confirmed": "#3b82f6",
    "registration": "#3b82f6",
    "in_progress": "#22c55e",
}

STATUS_LABELS = {
    "available": "فارغة",
    "occupied": "مشغولة",
    "maintenance": "صيانة",
    "reserved": "محجوزة",
    "active": "نشطة",
    "completed": "مكتملة",
    "cancelled": "ملغاة",
    "pending": "قيد الانتظار",
    "confirmed": "مؤكدة",
    "registration": "تسجيل",
    "in_progress": "جارية",
}

PAYMENT_METHOD_LABELS = {
    "cash": "كاش",
    "vodafone_cash": "فودافون كاش",
    "instapay": "إنستاباي",
    "bank_card": "بطاقة بنكية",
    "wallet": "محفظة",
}

ROLE_LABELS = {
    "admin": "مدير",
    "cashier": "كاشير",
    "supervisor": "مشرف",
}

SHIFT_LABELS = {
    "morning": "صباحي",
    "evening": "مسائي",
    "night": "ليلي",
}


def get_status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "#6b7280")


def get_status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def get_payment_label(method: str) -> str:
    return PAYMENT_METHOD_LABELS.get(method, method)


def get_role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def get_shift_label(shift: str) -> str:
    return SHIFT_LABELS.get(shift, shift)
"""Blog ilovasi uchun yordamchi funksiyalar."""
from datetime import datetime


def get_page_number(request, param='page', default=1):
    """Request dan xavfsiz sahifa raqamini oladi (paginatsiya uchun)."""
    try:
        n = int(request.GET.get(param, default))
        return max(1, n)
    except (ValueError, TypeError):
        return default


def parse_date(s):
    """Satrni sanaga aylantiradi (YYYY-MM-DD). Bo'sh yoki noto'g'ri bo'lsa None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

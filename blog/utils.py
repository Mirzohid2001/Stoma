"""Blog ilovasi uchun yordamchi funksiyalar."""


def get_page_number(request, param='page', default=1):
    """Request dan xavfsiz sahifa raqamini oladi (paginatsiya uchun)."""
    try:
        n = int(request.GET.get(param, default))
        return max(1, n)
    except (ValueError, TypeError):
        return default

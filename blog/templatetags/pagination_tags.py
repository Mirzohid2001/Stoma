from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def pagination_query(context, page_num):
    request = context.get('request')
    if not request:
        return f'?page={page_num}'
    get = request.GET.copy()
    get['page'] = page_num
    return '?' + get.urlencode()

from django import template

from web_site.models import Category

register = template.Library()

@register.simple_tag()
def get_categories():
    return Category.objects.all()

@register.simple_tag(name='is_auth_pages')
def check_auth_page(request):
    is_unique = request.path in ('/login/', '/registration/', '/create_article/')
    is_unique = is_unique or '/profile/' in request.path
    return is_unique

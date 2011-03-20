from django.template import Library
from django.conf import settings

register = Library()

# -----------------------------------------------

@register.inclusion_tag('snippet/post_tease.html')
def render_posts(pages, page_cur, page_para,posts):
    return {
        "pages": pages,
        "page_cur": page_cur,
        "page_para": page_para,
        'posts': posts,
    }

@register.inclusion_tag('snippet/sph_post_tease.html')
def render_sph_posts(res):
    return {
        "res": res,
    }


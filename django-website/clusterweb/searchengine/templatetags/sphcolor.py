from django import template
register = template.Library()

@register.filter(name='color')
def color(value, arg):
    return '<font color="%s">%s</font>' % (arg, value)


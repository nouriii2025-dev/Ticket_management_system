from django import template

register = template.Library()

@register.filter
def duration_hm(td):
    if not td:
        return ""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours} hr {minutes} min"
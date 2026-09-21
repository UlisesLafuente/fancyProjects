import gi

gi.require_version("Graphene", "1.0")

from gi.repository import Graphene


def scroll_into_view(scrolled_window, content, widget, margin=12):
    if widget is None or content is None:
        return
    if not widget.get_mapped() or not content.get_mapped():
        return
    result = widget.compute_point(content, Graphene.Point().init(0, 0))
    if result is None:
        return
    if isinstance(result, tuple):
        success, point = result[0], result[1]
    else:
        success, point = True, result
    if not success or point is None:
        return
    adjustment = scrolled_window.get_vadjustment()
    if adjustment is None:
        return
    upper = max(adjustment.get_upper() - adjustment.get_page_size(), 0.0)
    value = min(max(point.y - margin, 0.0), upper)
    adjustment.set_value(value)
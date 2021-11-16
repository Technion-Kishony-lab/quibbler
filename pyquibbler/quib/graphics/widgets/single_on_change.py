from matplotlib.widgets import AxesWidget


class Callback:

    def __init__(self, func=None):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def set_func_callback_on_widget_one_time(event_name: str, widget: AxesWidget, func, set_method_callback):
    events_to_callbacks = getattr(widget, '_events_to_quibbler_callbacks', {})
    callback = events_to_callbacks.get(event_name, Callback())
    if callback.func is None:
        set_method_callback(callback)
    callback.func = func
    events_to_callbacks[event_name] = callback
    setattr(widget, '_events_to_quibbler_callbacks', events_to_callbacks)

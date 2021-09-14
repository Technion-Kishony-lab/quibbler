# PyQuibbler

## DOC

### Interface

- `iquib`
- `Quib.get_value()`
- `DefaultFunctionQuib.is_cache_valid`
- `Quib.get_caching_method()`
- `Quib.set_caching_method()`

### Debugging

- `FunctionQuib._func`
- `FunctionQuib._args`
- `FunctionQuib._kwargs`
- `FunctionQuib._get_dependencies()`

#### Quib properties

## Q/A

- Why do changes not occur after doing `plt.show(block=False); # my_stuff; time.sleep(1000)`
  - The event loop needs to run- we tried doing `flush_events` but the only way (we saw on mac)
    for events to happen is to actually start the event loop (this happens automatically when pausing). <br/>
    As a side note, our solution (of ```axes.redraw_in_frame(); axes.figure.canvas.blit()```)
    has near identical performance to running the event loop ) <br/>
    It is important to note that we're not sure of all of this for other backends.
- Why don't the GUI tests run in CI?
  - We don't know yet, some works needs to be done to understand why the image is different on the server and the local
    tests
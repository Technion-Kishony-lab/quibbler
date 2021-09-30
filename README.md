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
- `FunctionQuib.get_cache_behavior()`

### Deepcopy

There are three cases in which we deepcopy:

#### Quib Creation

When a function quib is created, we deepcopy the arguments passed to the function. An example in which this is needed is
below:

```python
a = []
fquib = func(a, quib)
a.append(1)
fquib.get_value()
# Without deepcopy, the argument was mutated before the call
```

#### Function call

When a function quib calls the original function with quib values, we have to replace quibs with their values, which
requires us to recurse over the arguments to some extent. In addition, if a function mutates its arguments, stores them
in a global storage, returns them, or a view to them
(see Array copy/view behavior below) a user might get a handle to the internal arg storage of the function quib:

```python
@quib_func
def f(a):
    return a


quib = iquib([])
fquib = f(quib)
new_a = fquib.get_value()
new_a.append(1)
# Without deepcopy, the internal arg storage of fquib was mutated
```

Also, the user can mutate the result of `get_value` and by that unknowingly mutate the internal cache of the quib:

```python
q = iquib([0])
a = q.get_value()
a.append(1)
# Without deepcopy, we have changed the iquib without invalidating anything.
```

#### Cache storage

When a result of a function is stored in the cache, it should be deepcopied as well. A function might return an object
that has other references to it (a global object, a view, etc.)
and therefore mutation of that object will result in mutation of the internal cache. For example:

```python
A = []


def f():
    return A


result = f().get_value()
A.append(1)
# Without deepcopy, the result is mutated 
```

#### Cache usage

When a cached value is used, if the program receives a reference to the internal cache object, it could mutate it, even
by just applying overrides to it. So values fetched from the cache should be deepcopied.

#### Optimizations

We could:

- Have a whitelist of functions that don't need argument/result deepcopy (most numpy functions).
- Avoid deepcopying objects that have refcount=1
  (although the scan will still have to be recursive in case the object contains another with refcount>1)
- Let the user explicitly turn off deepcopying, globally or for specific functions
- Not support specific types of functions, or provide special decorators for functions that don't return new data
- Analyze functions to automatically discover if they need deepcopying or not
- Not cache user functions, or let users explicitly choose the function type if they want to cache

#### Array copy/view behavior

In some cases, an operation on a numpy array can result with a view to that numpy array, instead of a new array
referencing new memory. For example:

- `np.view(arr)`
- `arr[4:10]`
- `arr.reshape((3, 5))`
- `arr.swapaxes((1, 2))`

Some functions can return both a view and a copy, according to the arguments. For example `__getitem__` will return a
copy only if the selected data is contiguous in memory. On view arrays, the attribute `base` points to the original
array instead of `None`.

## Q/A

- Why do changes not occur after doing `plt.show(block=False); # my_stuff; time.sleep(1000)`
    - The event loop needs to run- we tried doing `flush_events` but the only way (we saw on mac)
      for events to happen is to actually start the event loop (this happens automatically when pausing). <br/>
      As a side note, our solution (of ```axes.redraw_in_frame(); axes.figure.canvas.blit()```)
      has near identical performance to running the event loop ) <br/>
      It is important to note that we're not sure of all of this for other backends.

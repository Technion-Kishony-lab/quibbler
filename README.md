# PyQuibbler

## Ideas for optimization

- Detect if a change actually occured before invalidating children
- Use weakref for results that lost the time/space cache tradeoff

## Notes

- Document GUI mac issue

## TODO

- Are `iter_quibs_in_object` and `deep_copy_and_replace_quibs_with_vals` good enough?
  - Consider using external lib
  - Support dict, list, set, frozenset, tuple, ndarray (both in code and tests)
- What happens when a quib(1) is plotted and a user drags it?
- Allow continuous update in graphics
- Keep an integer as integer while dragging
- if debug check that iquib does not contain quib
- protect user from setting properties on graphics elements
- should we use `perf_counter` or `process_time` for the cache tradeoff? `process_time` doesn't measure sleep time 
from typing import Callable, Iterable, TypeVar


T = TypeVar('T')
 
def partition(pred: Callable[[T], bool], iterable: Iterable[T]) -> tuple[list[T], list[T]]:
  """Partition an iterable into two based on a predicate.

  Args:
    pred: A predicate function
    iterable: An iterable

  Returns:
    A tuple of two lists, the first containing the elements that satisfy the predicate, and the second containing the rest.
  """
  true_list = []
  false_list = []
  for item in iterable:
    if pred(item):
      true_list.append(item)
    else:
      false_list.append(item)
  return true_list, false_list
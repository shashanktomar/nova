from __future__ import annotations

import functools
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterator
from typing import (
    Any,
    Final,
    Generic,
    Literal,
    NoReturn,
    ParamSpec,
    TypeIs,
    TypeVar,
)

from .result import Err, Ok

################################################################
# This file is inspired by Rust's std::Option type and follows
# the same pattern as the Result type in result.py. Its mostly
# written by claude 3.7
################################################################

T = TypeVar("T", covariant=True)  # Value type  # noqa: PLC0105
U = TypeVar("U")
P = ParamSpec("P")
R = TypeVar("R")


class Some(Generic[T]):
    """
    A type that represents the presence of a value.
    """

    __match_args__ = ("some_value",)
    __slots__ = ("_value",)

    def __iter__(self) -> Iterator[T]:
        yield self._value

    def __init__(self, value: T) -> None:
        self._value = value

    def __repr__(self) -> str:
        return f"Some({self._value!r})"

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        return isinstance(other, Some) and self._value == other._value

    def __ne__(self, other: Any) -> bool:  # noqa: ANN401
        return not (self == other)

    def __hash__(self) -> int:
        return hash((True, self._value))

    def is_some(self) -> Literal[True]:
        """
        Return `True` if the option is a `Some` value.
        """
        return True

    def is_none(self) -> Literal[False]:
        """
        Return `True` if the option is a `None` value.
        """
        return False

    def unwrap(self) -> T:
        """
        Returns the contained `Some` value.
        """
        return self._value

    def unwrap_or(self, _: object) -> T:
        """
        Returns the contained `Some` value or a provided default.
        """
        return self._value

    def unwrap_or_else(self, _: Callable[[], U]) -> T:
        """
        Returns the contained `Some` value or computes it from a closure.
        """
        return self._value

    def expect(self, _: str) -> T:
        """
        Returns the contained `Some` value.
        """
        return self._value

    def map(self, f: Callable[[T], U]) -> Some[U]:
        """
        Maps an `Option<T>` to `Option<U>` by applying a function to a contained value.
        """
        return Some(f(self._value))

    async def map_async(self, f: Callable[[T], Awaitable[U]]) -> Some[U]:
        """
        Maps an `Option<T>` to `Option<U>` by applying an async function to a contained value.
        """
        return Some(await f(self._value))

    def map_or(self, _: U, f: Callable[[T], U]) -> U:
        """
        Applies a function to the contained value (if any), or returns the provided default.
        """
        return f(self._value)

    def map_or_else(self, _: Callable[[], U], f: Callable[[T], U]) -> U:
        """
        Applies a function to the contained value (if any), or computes a default.
        """
        return f(self._value)

    def ok_or(self, _: object) -> Ok[T]:
        """
        Transforms the `Option<T>` into a `Result<T, E>`, mapping `Some(v)` to `Ok(v)` and `None` to `Err(err)`.
        """
        return Ok(self._value)

    def ok_or_else(self, _: Callable[[], object]) -> Ok[T]:
        """
        Transforms the `Option<T>` into a `Result<T, E>`, mapping `Some(v)` to `Ok(v)` and `None` to `Err(err_fn())`.
        """
        return Ok(self._value)

    def and_then(self, f: Callable[[T], Option[U]]) -> Option[U]:
        """
        Returns `None` if the option is `None`, otherwise calls `f` with the contained value and returns the result.
        """
        return f(self._value)

    async def and_then_async(self, f: Callable[[T], Awaitable[Option[U]]]) -> Option[U]:
        """
        Returns `None` if the option is `None`, otherwise calls async `f` with the contained value
        and returns the result.
        """
        return await f(self._value)

    def or_else(self, _: Callable[[], Option[T]]) -> Some[T]:
        """
        Returns the option if it contains a value, otherwise calls `f` and returns the result.
        """
        return self

    def filter(self, predicate: Callable[[T], bool]) -> Option[T]:
        """
        Returns `None` if the option is `None`, otherwise calls predicate with the wrapped value and returns:
        - `Some(t)` if predicate returns true (where t is the wrapped value)
        - `None` if predicate returns false
        """
        if predicate(self._value):
            return self
        else:
            return NONE

    def inspect(self, f: Callable[[T], Any]) -> Option[T]:
        """
        Calls a function with a reference to the contained value (if `Some`).
        """
        f(self._value)
        return self

    @property
    def some_value(self) -> T:
        """
        Return the inner value.
        """
        return self._value


class DoNoneError(Exception):
    """
    This is used to signal to `do()` that the result is a `None` value,
    which short-circuits the generator and returns None.
    """

    pass


class _NoneSingleton:
    """
    A type that represents the absence of a value.
    """

    __slots__ = ()

    def __iter__(self) -> Iterator[NoReturn]:
        def _iter() -> Iterator[NoReturn]:
            # Exception will be raised when the iterator is advanced, not when it's created
            raise DoNoneError()
            yield  # This yield will never be reached, but is necessary to create a generator #pyright: ignore

        return _iter()

    def __repr__(self) -> str:
        return "None_"

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        return isinstance(other, _NoneSingleton)

    def __ne__(self, other: Any) -> bool:  # noqa: ANN401
        return not (self == other)

    def __hash__(self) -> int:
        return hash((False,))

    def is_some(self) -> Literal[False]:
        """
        Return `True` if the option is a `Some` value.
        """
        return False

    def is_none(self) -> Literal[True]:
        """
        Return `True` if the option is a `None` value.
        """
        return True

    def unwrap(self) -> NoReturn:
        """
        Raises an `UnwrapNoneError` if the value is `None`.
        """
        raise UnwrapNoneError(self, "Called `Option.unwrap()` on a `None` value")

    def unwrap_or(self, default: U) -> U:
        """
        Returns the contained `Some` value or a provided default.
        """
        return default

    def unwrap_or_else(self, f: Callable[[], U]) -> U:
        """
        Returns the contained `Some` value or computes it from a closure.
        """
        return f()

    def expect(self, msg: str) -> NoReturn:
        """
        Raises an `UnwrapNoneError` with a custom message if the value is `None`.
        """
        raise UnwrapNoneError(self, msg)

    def map(self, _: Callable[[Any], Any]) -> _NoneSingleton:
        """
        Maps an `Option<T>` to `Option<U>` by applying a function to a contained value.
        """
        return self

    async def map_async(self, _: Callable[[Any], Awaitable[Any]]) -> _NoneSingleton:
        """
        Maps an `Option<T>` to `Option<U>` by applying an async function to a contained value.
        """
        return self

    def map_or(self, default: U, _: Callable[[Any], Any]) -> U:
        """
        Applies a function to the contained value (if any), or returns the provided default.
        """
        return default

    def map_or_else(self, default: Callable[[], U], _: Callable[[Any], Any]) -> U:
        """
        Applies a function to the contained value (if any), or computes a default.
        """
        return default()

    def ok_or(self, err: object) -> Err:
        """
        Transforms the `Option<T>` into a `Result<T, E>`, mapping `Some(v)` to `Ok(v)` and `None` to `Err(err)`.
        """
        return Err(err)

    def ok_or_else(self, err_fn: Callable[[], object]) -> Err:
        """
        Transforms the `Option<T>` into a `Result<T, E>`, mapping `Some(v)` to `Ok(v)` and `None` to `Err(err_fn())`.
        """
        return Err(err_fn())

    def and_then(self, _: Callable[[Any], Option[Any]]) -> _NoneSingleton:
        """
        Returns `None` if the option is `None`, otherwise calls `f` with the contained value and returns the result.
        """
        return self

    async def and_then_async(self, _: Callable[[Any], Awaitable[Option[Any]]]) -> _NoneSingleton:
        """
        Returns `None` if the option is `None`, otherwise calls async `f` with the contained value
        and returns the result.
        """
        return self

    def or_else(self, f: Callable[[], Option[T]]) -> Option[T]:
        """
        Returns the option if it contains a value, otherwise calls `f` and returns the result.
        """
        return f()

    def filter(self, _: Callable[[Any], bool]) -> _NoneSingleton:
        """
        Returns `None` if the option is `None`, otherwise calls predicate with the wrapped value and returns:
        - `Some(t)` if predicate returns true (where t is the wrapped value)
        - `None` if predicate returns false
        """
        return self

    def inspect(self, _: Callable[[Any], Any]) -> _NoneSingleton:
        """
        Calls a function with a reference to the contained value (if `Some`).
        """
        return self


# Create a singleton instance of _NoneSingleton, similar to None in Python
NONE = _NoneSingleton()


# define Option as a generic type alias for use in type annotations
"""
A simple `Option` type inspired by Rust.
"""
type Option[T] = Some[T] | _NoneSingleton


"""
A type to use in `isinstance` checks.
This is purely for convenience sake, as you could also just write `isinstance(opt, (Some, _NoneSingleton))
"""
SomeNone: Final = (Some, _NoneSingleton)


class UnwrapNoneError(Exception):
    """
    Exception raised from ``.unwrap()`` and ``.expect()`` calls on a `None` value.
    """

    _option: Option[Any]

    def __init__(self, option: Option[Any], message: str) -> None:
        self._option = option
        super().__init__(message)

    @property
    def option(self) -> Option[Any]:
        """
        Returns the original option.
        """
        return self._option


def as_option(
    *exceptions: type[BaseException],
) -> Callable[[Callable[P, R]], Callable[P, Option[R]]]:
    """
    Make a decorator to turn a function into one that returns an ``Option``.

    Regular return values are turned into ``Some(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``None_``.
    """
    if not exceptions or not all(
        inspect.isclass(exception) and issubclass(exception, BaseException) for exception in exceptions
    ):
        raise TypeError("as_option() requires one or more exception types")

    def decorator(f: Callable[P, R]) -> Callable[P, Option[R]]:
        """
        Decorator to turn a function into one that returns an ``Option``.
        """

        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Option[R]:
            try:
                return Some(f(*args, **kwargs))
            except exceptions:
                return NONE

        return wrapper

    return decorator


def as_async_option(
    *exceptions: type[BaseException],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Option[R]]]]:
    """
    Make a decorator to turn an async function into one that returns an ``Option``.
    Regular return values are turned into ``Some(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``None_``.
    """
    if not exceptions or not all(
        inspect.isclass(exception) and issubclass(exception, BaseException) for exception in exceptions
    ):
        raise TypeError("as_async_option() requires one or more exception types")

    def decorator(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[Option[R]]]:
        """
        Decorator to turn a function into one that returns an ``Option``.
        """

        @functools.wraps(f)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Option[R]:
            try:
                return Some(await f(*args, **kwargs))
            except exceptions:
                return NONE

        return async_wrapper

    return decorator


def is_some(option: Option[T]) -> TypeIs[Some[T]]:
    """A type guard to check if an option contains a value

    Usage:

    ```python
    o: Option[int] = get_an_option()
    if is_some(o):
        o   # o is of type Some[int]
    elif is_none(o):
        o   # o is of type _NoneSingleton
    ```

    """
    return option.is_some()


def is_none(option: Option[T]) -> TypeIs[_NoneSingleton]:
    """A type guard to check if an option is None

    Usage:

    ```python
    o: Option[int] = get_an_option()
    if is_some(o):
        o   # o is of type Some[int]
    elif is_none(o):
        o   # o is of type _NoneSingleton
    ```

    """
    return option.is_none()


def do(gen: Generator[Option[T]]) -> Option[T]:
    """Do notation for Option (syntactic sugar for sequence of `and_then()` calls).

    Usage:

    ```python
    final_option: Option[float] = do(
            Some(len(x) + int(y) + 0.5)
            for x in Some("hello")
            for y in Some(True)
        )
    ```

    NOTE: If you exclude the type annotation e.g. `Option[float]`
    your type checker might be unable to infer the return type.
    To avoid an error, you might need to help it with the type hint.
    """
    try:
        return next(gen)
    except DoNoneError:
        return NONE
    except TypeError as te:
        # Turn this into a more helpful error message.
        # Python has strange rules involving turning generators involving `await`
        # into async generators, so we want to make sure to help the user clearly.
        if "'async_generator' object is not an iterator" in str(te):
            raise TypeError(
                "Got async_generator but expected generator. See the section on do notation in the README."
            ) from te
        raise te


async def do_async(gen: Generator[Option[T]] | AsyncGenerator[Option[T]]) -> Option[T]:
    """Async version of do. Example:

    ```python
    final_option: Option[float] = await do_async(
        Some(len(x) + int(y) + z)
            for x in await get_async_option_1()
            for y in await get_async_option_2()
            for z in get_sync_option_3()
        )
    ```

    NOTE: Python makes generators async in a counter-intuitive way.

    ```python
    # This is a regular generator:
        async def foo(): ...
        do(Some(1) for x in await foo())
    ```

    ```python
    # But this is an async generator:
        async def foo(): ...
        async def bar(): ...
        do(
            Some(1)
            for x in await foo()
            for y in await bar()
        )
    ```

    We let users try to use regular `do()`, which works in some cases
    of awaiting async values. If we hit a case like above, we raise
    an exception telling the user to use `do_async()` instead.
    See `do()`.

    However, for better usability, it's better for `do_async()` to also accept
    regular generators, as you get in the first case:

    ```python
    async def foo(): ...
        do(Some(1) for x in await foo())
    ```

    Furthermore, neither mypy nor pyright can infer that the second case is
    actually an async generator, so we cannot annotate `do_async()`
    as accepting only an async generator. This is additional motivation
    to accept either.
    """
    try:
        if isinstance(gen, AsyncGenerator):
            return await gen.__anext__()
        else:
            return next(gen)
    except DoNoneError:
        return NONE


def option(value: T | None) -> Option[T]:
    """
    Convert a value to an Option.
    If the value is None, return None.
    Otherwise, return Some(value).
    """
    if value is None:
        return NONE
    else:
        return Some(value)

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

################################################################
# This file is copied from https://github.com/rustedpy/result
# The repo is not maintained anymore and its pretty thin, so we copied the code here.
################################################################

T = TypeVar("T", covariant=True)  # Success type  # noqa: PLC0105
E = TypeVar("E", covariant=True)  # Error type  # noqa: PLC0105
U = TypeVar("U")
F = TypeVar("F")
P = ParamSpec("P")
R = TypeVar("R")
TBE = TypeVar("TBE", bound=BaseException)


class Ok(Generic[T]):
    """
    A value that indicates success and which stores arbitrary data for the return value.
    """

    __match_args__ = ("ok_value",)
    __slots__ = ("_value",)

    def __iter__(self) -> Iterator[T]:
        yield self._value

    def __init__(self, value: T) -> None:
        self._value = value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        return isinstance(other, Ok) and self._value == other._value

    def __ne__(self, other: Any) -> bool:  # noqa: ANN401
        return not (self == other)

    def __hash__(self) -> int:
        return hash((True, self._value))

    def is_ok(self) -> Literal[True]:
        """
        Returns `True` if the result is `Ok`.

        This function is typically used to check the success state before performing
        operations that are only valid on success values.

        Examples:
        ```python
        x = Ok(2)
        assert x.is_ok() is True

        x = Err("error")
        assert x.is_ok() is False

        # Commonly used for conditionals
        if result.is_ok():
            # Do something with the success value
            value = result.unwrap()
        ```
        """
        return True

    def is_err(self) -> Literal[False]:
        """
        Returns `False` if the result is `Ok`.

        This function is typically used to check the error state before performing
        operations that are only valid on error values.

        Examples:
        ```python
        x = Ok(2)
        assert x.is_err() is False

        x = Err("error")
        assert x.is_err() is True

        # Commonly used for conditionals
        if result.is_err():
            # Handle the error
            error = result.unwrap_err()
        ```
        """
        return False

    def ok(self) -> T:
        """
        Returns the contained `Ok` value.

        Because this function returns the contained value and this is the `Ok` variant,
        the returned value is always defined (not None).

        Examples:
        ```python
        x = Ok(2)
        assert x.ok() == 2

        x = Err("nothing here")
        assert x.ok() is None
        ```
        """
        return self._value

    def err(self) -> None:
        """
        Returns the contained `Err` value or `None` if the result is `Ok`.

        Examples:
        ```python
        x = Ok(2)
        assert x.err() is None

        x = Err("error message")
        assert x.err() == "error message"
        ```
        """
        return None

    @property
    def ok_value(self) -> T:
        """
        Returns the contained `Ok` value as a property.

        This property provides direct access to the underlying value in the `Ok` variant.
        Unlike the `ok()` method, this property is only available on `Ok` instances.

        Examples:
        ```python
        x = Ok(2)
        assert x.ok_value == 2

        # Using pattern matching with structural pattern matching
        match result:
            case Ok(value):
                print(f"Got value: {value}")  # value is the same as result.ok_value
            case Err(err):
                print(f"Got error: {err}")
        ```
        """
        return self._value

    def expect(self, _: str) -> T:
        """
        Returns the contained value when called on an `Ok` variant, otherwise
        raises an UnwrapError with the provided message when called on an `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.expect("should not fail") == 2

        x = Err("oh no")
        try:
            x.expect("Failed to get value")  # raises UnwrapError
        except UnwrapError as e:
            assert "Failed to get value" in str(e)
        ```
        """
        return self._value

    def expect_err(self, message: str) -> NoReturn:
        """
        Returns the contained error when called on an `Err` variant, otherwise
        raises an UnwrapError with the provided message when called on an `Ok`.

        Examples:
        ```python
        x = Ok(2)
        try:
            x.expect_err("Expected error but got value")  # raises UnwrapError
        except UnwrapError as e:
            assert "Expected error but got value" in str(e)

        x = Err("oh no")
        assert x.expect_err("Should not fail") == "oh no"
        ```
        """
        raise UnwrapError(self, message)

    def unwrap(self) -> T:
        """
        Returns the contained `Ok` value or raises an UnwrapError if `self` is an `Err`.

        This is similar to `expect` but with a standard error message.
        Use `unwrap` only when you are confident that the value is `Ok`.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap() == 2

        x = Err("oh no")
        try:
            x.unwrap()  # raises UnwrapError
        except UnwrapError:
            # Handle the error
            pass
        ```
        """
        return self._value

    def unwrap_err(self) -> NoReturn:
        """
        Returns the contained `Err` value or raises an UnwrapError if `self` is an `Ok`.

        This is similar to `expect_err` but with a standard error message.
        Use `unwrap_err` only when you are confident that the value is `Err`.

        Examples:
        ```python
        x = Err("oh no")
        assert x.unwrap_err() == "oh no"

        x = Ok(2)
        try:
            x.unwrap_err()  # raises UnwrapError
        except UnwrapError:
            # Handle the error
            pass
        ```
        """
        raise UnwrapError(self, "Called `Result.unwrap_err()` on an `Ok` value")

    def unwrap_or(self, _: object) -> T:
        """
        Returns the contained `Ok` value or the provided default value.

        This method returns the contained value if `self` is an `Ok`, or the provided
        default value if `self` is an `Err`. Unlike `unwrap()`, this method never raises
        an exception.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or(0) == 2

        x = Err("error")
        assert x.unwrap_or(0) == 0
        ```
        """
        return self._value

    def unwrap_or_else(self, _: object) -> T:
        """
        Returns the contained `Ok` value or computes a value from the error.

        This method returns the contained value if `self` is an `Ok`, or applies the
        given function to the contained error value and returns the result if `self`
        is an `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or_else(lambda e: len(e)) == 2

        x = Err("error")
        assert x.unwrap_or_else(lambda e: len(e)) == 5  # length of "error"

        # Can be used for custom error handling
        x = Err("error")
        assert x.unwrap_or_else(lambda e: int(e) if e.isdigit() else 0) == 0
        ```
        """
        return self._value

    def unwrap_or_raise(self, _: object) -> T:
        """
        Returns the contained `Ok` value or raises the specified exception type with the error value.

        If `self` is `Ok`, returns the contained value. If `self` is `Err`, raises the provided
        exception type, initialized with the contained error value.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or_raise(ValueError) == 2

        x = Err("invalid input")
        try:
            x.unwrap_or_raise(ValueError)  # raises ValueError("invalid input")
        except ValueError as e:
            assert str(e) == "invalid input"

        # This is useful for converting Result error handling to exception handling
        def parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Could not parse '{s}' as integer")

        # Later in code:
        value = parse_int("10").unwrap_or_raise(ValueError)  # Returns 10
        value = parse_int("abc").unwrap_or_raise(ValueError)  # Raises ValueError
        ```
        """
        return self._value

    def unwrap_or_raise_with(self, _: Callable[[E], Exception]) -> T:
        """
        Returns the contained `Ok` value or raises the specified exception after applying the mapper.

        This method is called when the result is already `Ok`. It ignores the provided
        exception mapper and returns the contained value.
        """
        return self._value

    def map(self, op: Callable[[T], U]) -> Ok[U]:
        """
        Maps a `Result[T, E]` to `Result[U, E]` by applying a function to the contained value.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result wrapped in a new `Ok`. If `self` is `Err`, returns the original error unchanged.

        Examples:
        ```python
        # Transform a number
        x = Ok(2)
        assert x.map(lambda n: n * 2).unwrap() == 4

        # Transform a string
        x = Ok("hello")
        assert x.map(lambda s: s.upper()).unwrap() == "HELLO"

        # Error case remains unchanged
        x = Err("error")
        assert x.map(lambda s: s.upper()).unwrap_err() == "error"
        ```
        """
        return Ok(op(self._value))

    async def map_async(self, op: Callable[[T], Awaitable[U]]) -> Ok[U]:
        """
        Maps a `Result[T, E]` to `Result[U, E]` by applying an async function to the contained value.

        This is the asynchronous version of `map()`. If `self` is `Ok`, applies the provided
        async function to the contained value and returns the result wrapped in a new `Ok`.
        If `self` is `Err`, returns the original error unchanged.

        Examples:
        ```python
        async def double(n: int) -> int:
            await asyncio.sleep(0.1)
            return n * 2

        x = Ok(2)
        result = await x.map_async(double)
        assert result.unwrap() == 4

        x = Err("error")
        result = await x.map_async(double)
        assert result.unwrap_err() == "error"
        ```
        """
        return Ok(await op(self._value))

    def map_or(self, _: object, op: Callable[[T], U]) -> U:
        """
        Returns the provided function result applied to the contained value.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result. If `self` is `Err`, returns the provided default value.

        Examples:
        ```python
        x = Ok("foo")
        assert x.map_or(42, lambda s: len(s)) == 3

        x = Err("bar")
        assert x.map_or(42, lambda s: len(s)) == 42
        ```
        """
        return op(self._value)

    def map_or_else(self, _: object, op: Callable[[T], U]) -> U:
        """
        Returns the provided function result applied to the contained value.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result. If `self` is `Err`, applies the provided default function to the error
        value and returns its result.

        Examples:
        ```python
        x = Ok("foo")
        assert x.map_or_else(
            lambda e: len(e) + 1,  # default function
            lambda s: len(s)       # success function
        ) == 3

        x = Err("bar")
        assert x.map_or_else(
            lambda e: len(e) + 1,
            lambda s: len(s)
        ) == 4
        ```
        """
        return op(self._value)

    def map_err(self, _: object) -> Ok[T]:
        """
        Maps a `Result[T, E]` to `Result[T, F]` by applying a function to the contained error.

        If `self` is `Ok`, returns the original value unchanged. If `self` is `Err`, applies
        the provided function to the contained error value and returns the result wrapped in
        a new `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.map_err(lambda e: f"Error: {e}").unwrap() == 2

        x = Err("not found")
        assert x.map_err(lambda e: f"Error: {e}").unwrap_err() == "Error: not found"
        ```
        """
        return self

    def and_then(self, op: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """
        Calls the provided function with the contained value if the result is `Ok`,
        otherwise returns the `Err` value.

        This is useful for chaining operations that might fail.

        Note: This is the equivalent of Rust's `and_then` method.

        Examples:
        ```python
        # When result is Ok, function is applied:
        def square(x: int) -> Result[int, str]:
            return Ok(x * x)

        assert Ok(2).and_then(square).unwrap() == 4

        # When result is Err, function is not called:
        assert Err("error").and_then(square).unwrap_err() == "error"

        # Can be chained:
        def validate_positive(x: int) -> Result[int, str]:
            return Ok(x) if x > 0 else Err("negative number")

        assert Ok(5).and_then(validate_positive).and_then(square).unwrap() == 25
        assert Ok(-5).and_then(validate_positive).and_then(square).unwrap_err() == "negative number"
        ```
        """
        return op(self._value)

    async def and_then_async(self, op: Callable[[T], Awaitable[Result[U, E]]]) -> Result[U, E]:
        """
        The contained result is `Ok`, so return the result of `op` with the
        original value passed in
        """
        return await op(self._value)

    def or_(self, _: Result[T, F]) -> Result[T, E]:
        """
        Behaviour:
        If the result is `Ok`, returns the original value.
        If the result is `Err`, returns the provided `res` value.

        Note: Method is named `or_` with underscore because `or` is a Python reserved keyword.

        Examples:
        ```python
        # If self is Ok, return self regardless of the argument
        assert Ok(1).or_(Ok(2)).unwrap() == 1
        assert Ok(1).or_(Err("error")).unwrap() == 1

        # Chaining works as expected
        assert Ok(1).or_(Ok(2)).or_(Ok(3)).unwrap() == 1
        ```
        """
        return self

    def or_else(self, _: object) -> Ok[T]:
        """
        Returns the original `Ok` value without applying the provided function.

        This method is called when the result is already `Ok`. It ignores the provided function
        and returns the original `Ok` value unchanged.

        Examples:
        ```python
        # When result is Ok, function is not called:
        x = Ok(2)
        assert x.or_else(lambda e: Ok(3)).unwrap() == 2

        # Can be chained with other operations:
        x = Ok(2)
        assert x.or_else(lambda e: Ok(3)).map(lambda n: n * 2).unwrap() == 4
        ```
        """
        return self

    def inspect(self, op: Callable[[T], Any]) -> Result[T, E]:
        """
        Calls a function with the contained value if `Ok`. Returns the original result.
        """
        op(self._value)
        return self

    def inspect_err(self, _: Callable[[E], Any]) -> Result[T, E]:
        """
        Calls a function with the contained value if `Err`. Returns the original result.
        """
        return self


class DoError(Exception):
    """
    This is used to signal to `do()` that the result is an `Err`,
    which short-circuits the generator and returns that Err.
    Using this exception for control flow in `do()` allows us
    to simulate `and_then()` in the Err case: namely, we don't call `op`,
    we just return `self` (the Err).
    """

    def __init__(self, err: Err[E]) -> None:
        self.err = err


class Err(Generic[E]):
    """
    A value that signifies failure and which stores arbitrary data for the error.
    """

    __match_args__ = ("err_value",)
    __slots__ = ("_value",)

    def __iter__(self) -> Iterator[NoReturn]:
        def _iter() -> Iterator[NoReturn]:
            # Exception will be raised when the iterator is advanced, not when it's created
            raise DoError(self)
            yield  # This yield will never be reached, but is necessary to create a generator #pyright: ignore

        return _iter()

    def __init__(self, value: E) -> None:
        self._value = value

    def __repr__(self) -> str:
        return f"Err({self._value!r})"

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        return isinstance(other, Err) and self._value == other._value

    def __ne__(self, other: Any) -> bool:  # noqa: ANN401
        return not (self == other)

    def __hash__(self) -> int:
        return hash((False, self._value))

    def is_ok(self) -> Literal[False]:
        """
        Returns `True` if the result is `Ok`.

        This function is typically used to check the success state before performing
        operations that are only valid on success values.

        Examples:
        ```python
        x = Ok(2)
        assert x.is_ok() is True

        x = Err("error")
        assert x.is_ok() is False

        # Commonly used for conditionals
        if result.is_ok():
            # Do something with the success value
            value = result.unwrap()
        ```
        """
        return False

    def is_err(self) -> Literal[True]:
        """
        Returns `True` if the result is `Err`.

        This function is typically used to check the error state before performing
        operations that are only valid on error values.

        Examples:
        ```python
        x = Ok(2)
        assert x.is_err() is False

        x = Err("error")
        assert x.is_err() is True

        # Commonly used for conditionals
        if result.is_err():
            # Handle the error
            error = result.unwrap_err()
        ```
        """
        return True

    def ok(self) -> None:
        """
        Returns the contained `Ok` value or `None` if the result is `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.ok() == 2

        x = Err("nothing here")
        assert x.ok() is None
        ```
        """
        return None

    def err(self) -> E:
        """
        Returns the contained `Err` value.

        Because this function returns the contained value and this is the `Err` variant,
        the returned value is always defined (not None).

        Examples:
        ```python
        x = Ok(2)
        assert x.err() is None

        x = Err("error message")
        assert x.err() == "error message"
        ```
        """
        return self._value

    @property
    def err_value(self) -> E:
        """
        Returns the contained `Err` value as a property.

        This property provides direct access to the underlying value in the `Err` variant.
        Unlike the `err()` method, this property is only available on `Err` instances.

        Examples:
        ```python
        x = Err("oh no")
        assert x.err_value == "oh no"

        # Using pattern matching with structural pattern matching
        match result:
            case Ok(value):
                print(f"Got value: {value}")
            case Err(err):
                print(f"Got error: {err}")  # err is the same as result.err_value
        ```
        """
        return self._value

    def expect(self, message: str) -> NoReturn:
        """
        Returns the contained value when called on an `Ok` variant, otherwise
        raises an UnwrapError with the provided message when called on an `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.expect("should not fail") == 2

        x = Err("oh no")
        try:
            x.expect("Failed to get value")  # raises UnwrapError
        except UnwrapError as e:
            assert "Failed to get value" in str(e)
        ```
        """
        exc = UnwrapError(
            self,
            f"{message}: {self._value!r}",
        )
        if isinstance(self._value, BaseException):
            raise exc from self._value
        raise exc

    def expect_err(self, _: str) -> E:
        """
        Returns the contained error when called on an `Err` variant, otherwise
        raises an UnwrapError with the provided message when called on an `Ok`.

        Examples:
        ```python
        x = Ok(2)
        try:
            x.expect_err("Expected error but got value")  # raises UnwrapError
        except UnwrapError as e:
            assert "Expected error but got value" in str(e)

        x = Err("oh no")
        assert x.expect_err("Should not fail") == "oh no"
        ```
        """
        return self._value

    def unwrap(self) -> NoReturn:
        """
        Returns the contained `Ok` value or raises an UnwrapError if `self` is an `Err`.

        This is similar to `expect` but with a standard error message.
        Use `unwrap` only when you are confident that the value is `Ok`.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap() == 2

        x = Err("oh no")
        try:
            x.unwrap()  # raises UnwrapError
        except UnwrapError:
            # Handle the error
            pass
        ```
        """
        exc = UnwrapError(
            self,
            f"Called `Result.unwrap()` on an `Err` value: {self._value!r}",
        )
        if isinstance(self._value, BaseException):
            raise exc from self._value
        raise exc

    def unwrap_err(self) -> E:
        """
        Returns the contained `Err` value or raises an UnwrapError if `self` is an `Ok`.

        This is similar to `expect_err` but with a standard error message.
        Use `unwrap_err` only when you are confident that the value is `Err`.

        Examples:
        ```python
        x = Err("oh no")
        assert x.unwrap_err() == "oh no"

        x = Ok(2)
        try:
            x.unwrap_err()  # raises UnwrapError
        except UnwrapError:
            # Handle the error
            pass
        ```
        """
        return self._value

    def unwrap_or(self, default: U) -> U:
        """
        Returns the contained `Ok` value or the provided default value.

        This method returns the contained value if `self` is an `Ok`, or the provided
        default value if `self` is an `Err`. Unlike `unwrap()`, this method never raises
        an exception.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or(0) == 2

        x = Err("error")
        assert x.unwrap_or(0) == 0
        ```
        """
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """
        Returns the contained `Ok` value or computes a value from the error.

        This method returns the contained value if `self` is an `Ok`, or applies the
        given function to the contained error value and returns the result if `self`
        is an `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or_else(lambda e: len(e)) == 2

        x = Err("error")
        assert x.unwrap_or_else(lambda e: len(e)) == 5  # length of "error"

        # Can be used for custom error handling
        x = Err("error")
        assert x.unwrap_or_else(lambda e: int(e) if e.isdigit() else 0) == 0
        ```
        """
        return op(self._value)

    def unwrap_or_raise(self, e: type[TBE]) -> NoReturn:
        """
        Returns the contained `Ok` value or raises the specified exception type with the error value.

        If `self` is `Ok`, returns the contained value. If `self` is `Err`, raises the provided
        exception type, initialized with the contained error value.

        Examples:
        ```python
        x = Ok(2)
        assert x.unwrap_or_raise(ValueError) == 2

        x = Err("invalid input")
        try:
            x.unwrap_or_raise(ValueError)  # raises ValueError("invalid input")
        except ValueError as e:
            assert str(e) == "invalid input"

        # This is useful for converting Result error handling to exception handling
        def parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"Could not parse '{s}' as integer")

        # Later in code:
        value = parse_int("10").unwrap_or_raise(ValueError)  # Returns 10
        value = parse_int("abc").unwrap_or_raise(ValueError)  # Raises ValueError
        ```
        """
        raise e(self._value)

    def unwrap_or_raise_with(self, op: Callable[[E], Exception]) -> NoReturn:
        """
        Raises an exception by applying the provided function to the contained error value.

        This method is useful when you want to convert a specific error type to a custom
        exception type.
        """
        raise op(self._value)

    def map(self, _: object) -> Err[E]:
        """
        Maps a `Result[T, E]` to `Result[U, E]` by applying a function to the contained value.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result wrapped in a new `Ok`. If `self` is `Err`, returns the original error unchanged.

        Examples:
        ```python
        # Transform a number
        x = Ok(2)
        assert x.map(lambda n: n * 2).unwrap() == 4

        # Transform a string
        x = Ok("hello")
        assert x.map(lambda s: s.upper()).unwrap() == "HELLO"

        # Error case remains unchanged
        x = Err("error")
        assert x.map(lambda s: s.upper()).unwrap_err() == "error"
        ```
        """
        return self

    async def map_async(self, _: object) -> Err[E]:
        """
        Maps a `Result[T, E]` to `Result[U, E]` by applying an async function to the contained value.

        This is the asynchronous version of `map()`. If `self` is `Ok`, applies the provided
        async function to the contained value and returns the result wrapped in a new `Ok`.
        If `self` is `Err`, returns the original error unchanged.

        Examples:
        ```python
        async def double(n: int) -> int:
            await asyncio.sleep(0.1)
            return n * 2

        x = Ok(2)
        result = await x.map_async(double)
        assert result.unwrap() == 4

        x = Err("error")
        result = await x.map_async(double)
        assert result.unwrap_err() == "error"
        ```
        """
        return self

    def map_or(self, default: U, _: object) -> U:
        """
        Returns the provided default value.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result. If `self` is `Err`, returns the provided default value.

        Examples:
        ```python
        x = Ok("foo")
        assert x.map_or(42, lambda s: len(s)) == 3

        x = Err("bar")
        assert x.map_or(42, lambda s: len(s)) == 42
        ```
        """
        return default

    def map_or_else(self, default_op: Callable[[], U], _: object) -> U:
        """
        Returns the result of the provided default function.

        If `self` is `Ok`, applies the provided function to the contained value and returns
        the result. If `self` is `Err`, applies the provided default function to the error
        value and returns its result.

        Examples:
        ```python
        x = Ok("foo")
        assert x.map_or_else(
            lambda e: len(e) + 1,  # default function
            lambda s: len(s)       # success function
        ) == 3

        x = Err("bar")
        assert x.map_or_else(
            lambda e: len(e) + 1,
            lambda s: len(s)
        ) == 4
        ```
        """
        return default_op()

    def map_err(self, op: Callable[[E], F]) -> Err[F]:
        """
        Maps a `Result[T, E]` to `Result[T, F]` by applying a function to the contained error.

        If `self` is `Ok`, returns the original value unchanged. If `self` is `Err`, applies
        the provided function to the contained error value and returns the result wrapped in
        a new `Err`.

        Examples:
        ```python
        x = Ok(2)
        assert x.map_err(lambda e: f"Error: {e}").unwrap() == 2

        x = Err("not found")
        assert x.map_err(lambda e: f"Error: {e}").unwrap_err() == "Error: not found"
        ```
        """
        return Err(op(self._value))

    def and_then(self, _: object) -> Err[E]:
        """
        Calls the provided function with the contained value if the result is `Ok`,
        otherwise returns the `Err` value.

        This is useful for chaining operations that might fail.

        Note: This is the equivalent of Rust's `and_then` method.

        Examples:
        ```python
        # When result is Ok, function is applied:
        def square(x: int) -> Result[int, str]:
            return Ok(x * x)

        assert Ok(2).and_then(square).unwrap() == 4

        # When result is Err, function is not called:
        assert Err("error").and_then(square).unwrap_err() == "error"

        # Can be chained:
        def validate_positive(x: int) -> Result[int, str]:
            return Ok(x) if x > 0 else Err("negative number")

        assert Ok(5).and_then(validate_positive).and_then(square).unwrap() == 25
        assert Ok(-5).and_then(validate_positive).and_then(square).unwrap_err() == "negative number"
        ```
        """
        return self

    async def and_then_async(self, _: object) -> Err[E]:
        """
        The contained result is `Err`, so return `Err` with the original value
        """
        return self

    def or_(self, res: Result[T, F]) -> Result[T, F]:
        """
        Behaviour:
        If the result is `Ok`, returns the original value.
        If the result is `Err`, returns the provided `res` value.

        Note: Method is named `or_` with underscore because `or` is a Python reserved keyword.

        Examples:
        ```python
        # If self is Err, return the argument
        assert Err("error").or_(Ok(2)).unwrap() == 2
        assert Err("error1").or_(Err("error2")).unwrap_err() == "error2"

        # Chaining works as expected
        assert Err("error1").or_(Err("error2")).or_(Ok(3)).unwrap() == 3
        assert Err("error1").or_(Ok(2)).or_(Ok(3)).unwrap() == 2
        ```
        """
        return res

    def or_else(self, op: Callable[[E], Result[T, F]]) -> Result[T, F]:
        """
        Calls the provided function with the contained error value if the result is `Err`,
        otherwise returns the original `Ok` value.

        This is useful for providing fallback operations when a result is an error.

        Examples:
        ```python
        # When result is Err, function is applied:
        def fallback(e: str) -> Result[int, str]:
            return Ok(0) if e == "empty" else Err("invalid")

        assert Err("empty").or_else(fallback).unwrap() == 0
        assert Err("error").or_else(fallback).unwrap_err() == "invalid"

        # When result is Ok, function is not called:
        assert Ok(2).or_else(fallback).unwrap() == 2

        # Can be chained with other operations:
        assert Err("empty").or_else(fallback).map(lambda n: n * 2).unwrap() == 0
        ```
        """
        return op(self._value)

    def inspect(self, _: Callable[[T], Any]) -> Result[T, E]:
        """
        Calls a function with the contained value if `Ok`. Returns the original result.
        """
        return self

    def inspect_err(self, op: Callable[[E], Any]) -> Result[T, E]:
        """
        Calls a function with the contained value if `Err`. Returns the original result.
        """
        op(self._value)
        return self


# define Result as a generic type alias for use
# in type annotations
"""
A simple `Result` type inspired by Rust.
Not all methods (https://doc.rust-lang.org/std/result/enum.Result.html)
have been implemented, only the ones that make sense in the Python context.
"""
type Result[T, E] = Ok[T] | Err[E]

"""
A type to use in `isinstance` checks.
This is purely for convenience sake, as you could also just write `isinstance(res, (Ok, Err))
"""
OkErr: Final = (Ok, Err)


class UnwrapError(Exception):
    """
    Exception raised from ``.unwrap_<...>`` and ``.expect_<...>`` calls.

    The original ``Result`` can be accessed via the ``.result`` attribute, but
    this is not intended for regular use, as type information is lost:
    ``UnwrapError`` doesn't know about both ``T`` and ``E``, since it's raised
    from ``Ok()`` or ``Err()`` which only knows about either ``T`` or ``E``,
    not both.
    """

    _result: Result[object, object]

    def __init__(self, result: Result[object, object], message: str) -> None:
        self._result = result
        super().__init__(message)

    @property
    def result(self) -> Result[Any, Any]:
        """
        Returns the original result.
        """
        return self._result


def as_result(
    *exceptions: type[TBE],
) -> Callable[[Callable[P, R]], Callable[P, Result[R, TBE]]]:
    """
    Make a decorator to turn a function into one that returns a ``Result``.

    Regular return values are turned into ``Ok(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``Err(exc)``.
    """
    if not exceptions or not all(
        inspect.isclass(exception) and issubclass(exception, BaseException) for exception in exceptions
    ):
        raise TypeError("as_result() requires one or more exception types")

    def decorator(f: Callable[P, R]) -> Callable[P, Result[R, TBE]]:
        """
        Decorator to turn a function into one that returns a ``Result``.
        """

        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R, TBE]:
            try:
                return Ok(f(*args, **kwargs))
            except exceptions as exc:
                return Err(exc)

        return wrapper

    return decorator


def as_async_result(
    *exceptions: type[TBE],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Result[R, TBE]]]]:
    """
    Make a decorator to turn an async function into one that returns a ``Result``.
    Regular return values are turned into ``Ok(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``Err(exc)``.
    """
    if not exceptions or not all(
        inspect.isclass(exception) and issubclass(exception, BaseException) for exception in exceptions
    ):
        raise TypeError("as_result() requires one or more exception types")

    def decorator(
        f: Callable[P, Awaitable[R]],
    ) -> Callable[P, Awaitable[Result[R, TBE]]]:
        """
        Decorator to turn a function into one that returns a ``Result``.
        """

        @functools.wraps(f)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R, TBE]:
            try:
                return Ok(await f(*args, **kwargs))
            except exceptions as exc:
                return Err(exc)

        return async_wrapper

    return decorator


def is_ok(result: Result[T, E]) -> TypeIs[Ok[T]]:
    """A type guard to check if a result is an Ok

    Usage:

    ``` python
    r: Result[int, str] = get_a_result()
    if is_ok(r):
        r   # r is of type Ok[int]
    elif is_err(r):
        r   # r is of type Err[str]
    ```

    """
    return result.is_ok()


def is_err(result: Result[T, E]) -> TypeIs[Err[E]]:
    """A type guard to check if a result is an Err

    Usage:

    ``` python
    r: Result[int, str] = get_a_result()
    if is_ok(r):
        r   # r is of type Ok[int]
    elif is_err(r):
        r   # r is of type Err[str]
    ```

    """
    return result.is_err()


def do(gen: Generator[Result[T, E]]) -> Result[T, E]:
    """Do notation for Result (syntactic sugar for sequence of `and_then()` calls).


    Usage:

    ``` rust
    // This is similar to
    use do_notation::m;
    let final_result = m! {
        x <- Ok("hello");
        y <- Ok(True);
        Ok(len(x) + int(y) + 0.5)
    };
    ```

    ``` rust
    final_result: Result[float, int] = do(
            Ok(len(x) + int(y) + 0.5)
            for x in Ok("hello")
            for y in Ok(True)
        )
    ```

    NOTE: If you exclude the type annotation e.g. `Result[float, int]`
    your type checker might be unable to infer the return type.
    To avoid an error, you might need to help it with the type hint.
    """
    try:
        return next(gen)
    except DoError as e:
        out: Err[E] = e.err  # type: ignore
        return out
    except TypeError as te:
        # Turn this into a more helpful error message.
        # Python has strange rules involving turning generators involving `await`
        # into async generators, so we want to make sure to help the user clearly.
        if "'async_generator' object is not an iterator" in str(te):
            raise TypeError(
                "Got async_generator but expected generator.See the section on do notation in the README."
            ) from te
        raise te


async def do_async(
    gen: Generator[Result[T, E]] | AsyncGenerator[Result[T, E]],
) -> Result[T, E]:
    """Async version of do. Example:

    ``` python
    final_result: Result[float, int] = await do_async(
        Ok(len(x) + int(y) + z)
            for x in await get_async_result_1()
            for y in await get_async_result_2()
            for z in get_sync_result_3()
        )
    ```

    NOTE: Python makes generators async in a counter-intuitive way.

    ``` python
    # This is a regular generator:
        async def foo(): ...
        do(Ok(1) for x in await foo())
    ```

    ``` python
    # But this is an async generator:
        async def foo(): ...
        async def bar(): ...
        do(
            Ok(1)
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

    ``` python
    async def foo(): ...
        do(Ok(1) for x in await foo())
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
    except DoError as e:
        out: Err[E] = e.err  # type: ignore
        return out

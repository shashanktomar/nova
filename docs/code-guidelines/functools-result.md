# Functional Error Handling with Result Types

This document outlines the guidelines for using Result types and functional error handling patterns in the Luno codebase.

## Philosophy

We use functional error handling patterns inspired by Rust to achieve:

- **Type safety**: Errors are part of the function signature
- **Explicit handling**: Callers must handle both success and error cases
- **Composability**: Results can be chained and transformed
- **No hidden control flow**: No unexpected exceptions

## Expected vs Unexpected Errors

### Expected Errors

**Definition**: Errors that are part of normal program flow and business logic.

**Examples**:

- Authentication failures
- Insufficient permissions
- Business rule violations (e.g., insufficient funds)
- External service timeouts
- Rate limit exceeded
- Invalid state transitions
- Concurrent modification conflicts
- Third-party API errors

**Handling**: Use `Result[T, E]` types

```python
def authenticate(token: str) -> Result[User, AuthError]:
    # Returns Err for expected auth failures
    pass
```

### Unexpected Errors

**Definition**: Errors that indicate bugs, system failures, or programming errors.

**Examples**:

- Database connection failures
- Out of memory errors
- Assertion failures
- Type errors
- Null pointer exceptions

**Handling**: Use exceptions (raise/throw)

```python
class InstrumentRepo(Protocol):
    def get_by_ticker(self, ticker: str) -> Instrument | None:
        """Returns None if not found.

        Raises:
            RepoException: On database errors (unexpected)
        """
        pass
```

## When to Use Result vs Exceptions

### Use Result[T, E] when:

- The error is expected and recoverable
- The caller should handle the error case
- The error is part of the business logic
- You want to chain operations that might fail
- The error provides meaningful context for the caller

### Use Exceptions when:

- The error is unexpected (bug/system failure)
- The error is unrecoverable at this level
- The error indicates a programming mistake
- You're implementing a protocol/interface that doesn't use Result
- You're at system boundaries (database, network, file I/O)

## Basic Usage

### Importing

```python
from modules.core.functools.models import Result, Ok, Err, is_ok, is_err
```

### Creating Results

```python
# Success case
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

# With structured errors
class RateLimitError(BaseModel):
    limit: int
    reset_at: datetime
    message: str

def call_external_api(endpoint: str) -> Result[Response, RateLimitError]:
    if rate_limited:
        return Err(RateLimitError(
            limit=100,
            reset_at=datetime.now() + timedelta(hours=1),
            message="API rate limit exceeded"
        ))
    return Ok(response)
```

### Handling Results

```python
# Pattern matching (Python 3.10+)
result = divide(10, 2)
match result:
    case Ok(value):
        print(f"Result: {value}")
    case Err(error):
        print(f"Error: {error}")

# Using helper functions
if is_ok(result):
    value = result.unwrap()
    print(f"Success: {value}")
else:
    error = result.unwrap_err()
    print(f"Failed: {error}")

# Safe unwrapping with defaults
value = result.unwrap_or(0.0)
value = result.unwrap_or_else(lambda err: log_and_return_default(err))
```

## Advanced Patterns

### Chaining Operations

```python
# Transform success values
result = get_user(user_id).map(lambda u: u.email)

# Transform error values
result = parse_int(text).map_err(lambda e: f"Invalid number: {e}")

# Chain fallible operations
result = (
    get_user(user_id)
    .and_then(lambda u: validate_permissions(u))
    .and_then(lambda u: update_profile(u, data))
    .map(lambda u: u.id)
)

# Provide alternative results
result = primary_fetch().or_else(lambda _: fallback_fetch())
```

### Async Operations

```python
# Async transformations
async def fetch_user(id: int) -> Result[User, str]:
    result = await get_user_async(id)
    return result.map_async(lambda u: enrich_user_data(u))
```

### Collecting Results

```python
# Convert list of Results to Result of list
# Note: collect_results should be implemented when required

results = [process_item(item) for item in items]
# all_processed = collect_results(results)  # Result[list[Item], ProcessError]
```

## Error Modeling

### Define Errors as Pydantic Dataclasses

```python
from pydantic.dataclasses import dataclass
from modules.core.models.errors import BaseError
from modules.core.models.aliases import NonEmptyString

# Good: Structured error with context
@dataclass(kw_only=True)
class AuthenticationError(BaseError):
    reason: Literal["expired", "invalid", "revoked"]
    token_prefix: str
    msg: NonEmptyString = "Authentication failed"

@dataclass(kw_only=True)
class NotFoundError(BaseError):
    resource: str
    identifier: str
    msg: NonEmptyString = "Resource not found"

# Bad: String errors lack structure
def authenticate(token: str) -> Result[User, str]:
    return Err(f"Invalid token")  # Don't do this
```

## Best Practices

### 1. Be Explicit About Errors

```python
# Good: Clear error type in signature
def parse_config(path: str) -> Result[Config, ConfigError]:
    pass

# Bad: Generic error type
def parse_config(path: str) -> Result[Config, Exception]:
    pass
```

### 2. Handle Errors at the Right Level

```python
# Don't unwrap prematurely
def process_data(data: str) -> Result[Output, ProcessError]:
    # Good: Propagate error with context
    parsed = parse_json(data).map_err(
        lambda e: ProcessError(step="parsing", cause=str(e))
    )

    # Bad: Unwrap and lose error context
    try:
        parsed = parse_json(data).unwrap()
    except:
        return Err(ProcessError(step="unknown"))
```

### 3. Use Do-Notation for Complex Flows

```python
from modules.core.functools.models import do

def execute_trade(order: Order) -> Result[Trade, TradeError]:
    def _trade_flow():
        balance = yield check_balance(order.account_id)
        authorization = yield verify_trading_permissions(order.account_id)
        quote = yield get_market_quote(order.symbol)
        trade = yield submit_order(order, quote)
        return Ok(trade)

    return do(_trade_flow())
```

### 4. Document Error Cases

```python
def transfer_funds(from_id: str, to_id: str, amount: Decimal) -> Result[Transaction, TransferError]:
    """Transfer funds between accounts.

    Returns:
        Ok(Transaction): Successful transfer
        Err(TransferError): With one of:
            - error_code="INSUFFICIENT_FUNDS"
            - error_code="ACCOUNT_NOT_FOUND"
            - error_code="ACCOUNT_FROZEN"
            - error_code="LIMIT_EXCEEDED"
    """
```

## Anti-Patterns to Avoid

### 1. Don't Mix Paradigms

```python
# Bad: Returning Result but also raising exceptions
def bad_function() -> Result[int, str]:
    if condition:
        raise ValueError("Unexpected!")  # Don't do this
    return Ok(42)
```

### 2. Don't Use Result for Unexpected Errors

```python
# Bad: Database errors are unexpected
def get_user(id: int) -> Result[User, DatabaseError]:
    try:
        return Ok(db.query(f"SELECT * FROM users WHERE id={id}"))
    except DBConnectionError as e:
        return Err(DatabaseError(str(e)))  # Should raise instead
```

### 3. Don't Ignore Error Context

```python
# Bad: Losing error information
result.map_err(lambda _: "Something went wrong")

# Good: Preserve and enhance error context
result.map_err(lambda e: DetailedError(
    original=e,
    context="While processing user request",
    timestamp=datetime.now()
))
```

## Migration Strategy

When refactoring exception-based code to use Result types:

1. Start at the leaves (deepest functions)
2. Identify expected vs unexpected errors
3. Convert expected errors to Result types
4. Keep unexpected errors as exceptions
5. Update callers incrementally

```python
# Before
def execute_transfer(from_id: str, to_id: str, amount: Decimal) -> Transfer:
    if not has_sufficient_balance(from_id, amount):
        raise InsufficientFundsError()  # Expected error as exception
    return process_transfer(from_id, to_id, amount)

# After
def execute_transfer(from_id: str, to_id: str, amount: Decimal) -> Result[Transfer, TransferError]:
    balance = get_balance(from_id)  # Still raises on DB errors (unexpected)
    if balance < amount:
        return Err(TransferError(reason="insufficient_funds", available=balance))
    return Ok(process_transfer(from_id, to_id, amount))
```

## Summary

- Use `Result[T, E]` for **expected errors** that are part of business logic
- Use **exceptions** for unexpected errors (bugs, system failures)
- Model errors as **Pydantic models** for structure and type safety
- **Chain operations** with map, and_then, or_else for composability
- Be **explicit** about error types in function signatures
- Handle errors at the **appropriate level** with proper context

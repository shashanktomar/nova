
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from nova.utils.types import DirectUrl, GitHubRepo, GitUrl, NonEmptySequence, NonEmptyString


class _StringModel(BaseModel):
    value: NonEmptyString


class _SequenceModel(BaseModel):
    values: NonEmptySequence[str]


class _GitHubRepoModel(BaseModel):
    repo: GitHubRepo


class _GitUrlModel(BaseModel):
    url: GitUrl


class _DirectUrlModel(BaseModel):
    url: DirectUrl


@pytest.mark.parametrize("value", ["hello", "world", "0"])
def test_non_empty_string_accepts_non_empty(value: str) -> None:
    assert _StringModel(value=value).value == value


@pytest.mark.parametrize("value", [""])
def test_non_empty_string_rejects_empty(value: str) -> None:
    with pytest.raises(ValidationError):
        _StringModel(value=value)


@pytest.mark.parametrize(
    "values",
    [
        ("a",),
        ("a", "b"),
    ],
)
def test_non_empty_sequence(values: tuple[str, ...]) -> None:
    model = _SequenceModel(values=list(values))
    assert tuple(model.values) == values


@pytest.mark.parametrize("values", [(), ()])
def test_non_empty_sequence_rejects_empty(values: tuple[str, ...]) -> None:
    with pytest.raises(ValidationError):
        _SequenceModel(values=list(values))


@pytest.mark.parametrize(
    "repo",
    [
        "owner/repo",
        "Owner-123/repo_name",
        "org/repo.with.dots",
    ],
)
def test_github_repo_valid(repo: str) -> None:
    assert _GitHubRepoModel(repo=repo).repo == repo


@pytest.mark.parametrize(
    "repo",
    [
        "owner repo",
        "owner",
        "owner/repo/extra",
        "owner/",
        "/repo",
    ],
)
def test_github_repo_invalid(repo: str) -> None:
    with pytest.raises(ValidationError):
        _GitHubRepoModel(repo=repo)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo.git",
        "http://git.example.com/owner/repo",
        "git@github.com:owner/repo.git",
        "git://github.com/owner/repo.git",
    ],
)
def test_git_url_valid(url: str) -> None:
    assert _GitUrlModel(url=url).url == url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/repo.git",
        "ssh://example.com/repo",
        "owner/repo",
    ],
)
def test_git_url_invalid(url: str) -> None:
    with pytest.raises(ValidationError):
        _GitUrlModel(url=url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/marketplace.json",
        "http://example.com/file.json",
    ],
)
def test_direct_url_valid(url: str) -> None:
    assert str(_DirectUrlModel(url=url).url) == url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file.json",
        "file:///tmp/file.json",
    ],
)
def test_direct_url_invalid(url: str) -> None:
    with pytest.raises(ValidationError):
        _DirectUrlModel(url=url)

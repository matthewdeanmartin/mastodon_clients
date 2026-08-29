"""Error types shared across the data layer.

Validation deliberately accumulates rather than failing fast: an editor adding a
client wants every problem in their TOML at once, not one per `make validate`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class MawkingbirdError(Exception):
    """Base class for every error this package raises."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One problem found in the repository's data.

    `where` is a human-locatable path -- a file, or a file plus a dotted key --
    rather than a line number, because the TOML parsers do not report positions.
    """

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(slots=True)
class ValidationReport:
    """Accumulated issues from a validation pass."""

    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, where: str, message: str) -> None:
        self.issues.append(ValidationIssue(where, message))

    def extend(self, other: ValidationReport) -> None:
        self.issues.extend(other.issues)

    @property
    def ok(self) -> bool:
        return not self.issues

    def render(self) -> str:
        return "\n".join(f"  {issue}" for issue in self.issues)

    def raise_if_failed(self) -> None:
        if self.issues:
            raise ValidationError(self)


class ValidationError(MawkingbirdError):
    """Raised when a validation pass found at least one issue."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        count = len(report.issues)
        noun = "issue" if count == 1 else "issues"
        super().__init__(f"{count} validation {noun}:\n{report.render()}")

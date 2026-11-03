"""Trusted identity context for protected customer order queries.

The actual identity-verification flow is intentionally outside this data layer.
Only trusted application code should create this context after verification.
It must never be populated from model-generated function arguments.
"""

from __future__ import annotations

from src.data.exceptions import IdentityVerificationRequiredError

_VERIFIED_CONTEXT_PROOF = object()


class VerifiedCustomerContext:
    """Opaque context marking a customer identity verified by the application."""

    __slots__ = ("_customer_id", "_proof", "_locked")

    def __init__(self, customer_id: int, *, _proof: object | None = None) -> None:
        if _proof is not _VERIFIED_CONTEXT_PROOF:
            raise IdentityVerificationRequiredError(
                "A verified customer context can only be created by the trusted "
                "identity-verification flow."
            )
        if isinstance(customer_id, bool) or not isinstance(customer_id, int) or customer_id <= 0:
            raise IdentityVerificationRequiredError("O contexto deve identificar um cliente válido.")
        object.__setattr__(self, "_customer_id", customer_id)
        object.__setattr__(self, "_proof", _proof)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("VerifiedCustomerContext é imutável.")
        object.__setattr__(self, name, value)

    @property
    def customer_id(self) -> int:
        return self._customer_id

    @classmethod
    def _after_identity_verification(cls, customer_id: int) -> VerifiedCustomerContext:
        """Internal factory for the future trusted identity-verification layer."""
        return cls(customer_id, _proof=_VERIFIED_CONTEXT_PROOF)


def require_verified_customer(
    context: VerifiedCustomerContext | None,
) -> int:
    if (
        not isinstance(context, VerifiedCustomerContext)
        or context._proof is not _VERIFIED_CONTEXT_PROOF
    ):
        raise IdentityVerificationRequiredError(
            "Valide a identidade do cliente antes de consultar pedidos ou itens."
        )
    return context.customer_id

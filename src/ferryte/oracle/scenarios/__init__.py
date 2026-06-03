"""Built-in scenarios. Importing this package registers all of them."""

from . import cross_tenant, memory_poisoning, source_revocation, stale_fact  # noqa: F401

__all__ = ["source_revocation", "cross_tenant", "stale_fact", "memory_poisoning"]

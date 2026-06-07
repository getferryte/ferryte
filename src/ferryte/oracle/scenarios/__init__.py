"""Built-in scenarios. Importing this package registers all of them."""

from . import (  # noqa: F401
    cross_tenant,
    memory_poisoning,
    mosaic,
    source_revocation,
    stale_fact,
)

__all__ = ["source_revocation", "cross_tenant", "stale_fact", "memory_poisoning", "mosaic"]

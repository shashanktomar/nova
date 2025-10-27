from nova.datastore import DataStore
from nova.utils.functools.models import Result

from .models import MarketplaceState, MarketplaceStateError


class MarketplaceStore:
    def __init__(self, store: DataStore) -> None:
        self._store = store

    def save(self, state: MarketplaceState) -> Result[None, MarketplaceStateError]:
        return self._store.save(state.name, state.model_dump(mode="json")).map_err(
            lambda error: MarketplaceStateError(
                name=state.name,
                message=f"Failed to save marketplace state: {error.message}",
            )
        )

    def load(self, name: str) -> Result[MarketplaceState, MarketplaceStateError]:
        return self._store.load(name).map_err(
            lambda error: MarketplaceStateError(
                name=name,
                message=f"Failed to load marketplace state: {error.message}",
            )
        ).map(lambda state_data: MarketplaceState.model_validate(state_data))

    def delete(self, name: str) -> Result[None, MarketplaceStateError]:
        return self._store.delete(name).map_err(
            lambda error: MarketplaceStateError(
                name=name,
                message=f"Failed to delete marketplace state: {error.message}",
            )
        )

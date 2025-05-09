from typing import Any, Literal, override

type ImmichAssetType = Literal["IMAGE", "VIDEO", "AUDIO", "OTHER"]


class ImmichAsset:
    id: str
    filename: str
    asset_type: ImmichAssetType

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs["id"]
        self.filename = kwargs["originalFileName"]
        self.asset_type = kwargs["type"]

    @override
    def __repr__(self) -> str:
        return f'ImmichAsset({self.asset_type}, "{self.id}")'


class ImmichTag:
    id: str
    parent_id: str | None
    name: str
    full_name: str

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs["id"]
        self.name = kwargs["name"]
        self.full_name = kwargs["value"]
        self.parent_id = kwargs.get("parentId")

    @override
    def __repr__(self) -> str:
        return f'ImmichTag("{self.full_name}", "{self.id}")'

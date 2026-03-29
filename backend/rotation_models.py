from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import RefreshRun, TrendDataset


@dataclass(frozen=True)
class RotationTarget:
    code: str
    name: str
    quote_id: str
    security_type_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            'code': self.code,
            'name': self.name,
            'quoteId': self.quote_id,
            'securityTypeName': self.security_type_name,
        }


@dataclass(frozen=True)
class SectorRotationPayload:
    dataset: TrendDataset | None
    is_refreshing: bool
    last_run: RefreshRun | None
    targets: tuple[RotationTarget, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            'dataset': self.dataset,
            'isRefreshing': self.is_refreshing,
            'lastRun': self.last_run.to_dict() if self.last_run else None,
            'targets': [target.to_dict() for target in self.targets],
        }


DEFAULT_ROTATION_TARGETS = (
    RotationTarget(code='BK0428', name='电力', quote_id='90.BK0428', security_type_name='板块'),
    RotationTarget(code='BK1036', name='半导体', quote_id='90.BK1036', security_type_name='板块'),
    RotationTarget(code='BK0473', name='证券Ⅱ', quote_id='90.BK0473', security_type_name='板块'),
    RotationTarget(code='BK0475', name='银行Ⅱ', quote_id='90.BK0475', security_type_name='板块'),
    RotationTarget(code='BK1029', name='汽车整车', quote_id='90.BK1029', security_type_name='板块'),
    RotationTarget(code='BK1408', name='机器人', quote_id='90.BK1408', security_type_name='板块'),
)

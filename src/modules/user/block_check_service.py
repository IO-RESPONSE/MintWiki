"""사용자 차단 여부를 확인하는 서비스."""
from datetime import datetime

from modules.user.block_repository import BlockRepository


class BlockCheckService:
    """
    사용자가 현재 차단되어 있는지 확인하는 서비스.

    저장소에서 사용자의 차단 기록을 조회하고, 조회된 차단이 주어진
    시각 기준으로 유효한지 판단한다. 차단 기록이 없거나 만료된
    경우에는 차단되지 않은 것으로 간주한다. 이 서비스를 편집 등의
    권한 검사에 실제로 연결하는 작업은 이후 태스크에서 다룬다.
    """

    def __init__(self, block_repository: BlockRepository):
        """
        서비스를 초기화한다.

        Args:
            block_repository: 차단 조회에 사용할 저장소
        """
        self.block_repository = block_repository

    async def is_blocked(self, user_id: str, now: datetime) -> bool:
        """
        주어진 사용자가 now 시각 기준으로 차단되어 있는지 확인한다.

        Args:
            user_id: 확인할 사용자의 id
            now: 기준이 되는 시각

        Returns:
            유효한 차단이 존재하면 True, 아니면 False
        """
        block = await self.block_repository.get_by_user_id(user_id)
        if block is None:
            return False
        return block.is_active(now)

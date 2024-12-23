from dataclasses import dataclass
from typing import List
from lifeblocks.models.block import Block
from lifeblocks.models.timeblock import PickReason


@dataclass
class BlockQueue:
    blocks: List[Block]
    total_multiplier: float = 1.0
    pick_reason: PickReason = PickReason.NORMAL

    def __init__(self, initial_block: Block = None, pick_reason: PickReason = PickReason.NORMAL):
        self.blocks = []
        self.total_multiplier = 0
        self.pick_reason = pick_reason
        if initial_block:
            self.add_block(initial_block)

    def add_block(self, block: Block):
        self.blocks.append(block)
        self.total_multiplier += block.length_multiplier

    def is_full(self):
        return self.total_multiplier >= 1.0

    def has_space_for(self, block: Block):
        return self.total_multiplier + block.length_multiplier <= 1.0 
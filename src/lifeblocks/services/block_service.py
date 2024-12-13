from datetime import datetime
import random
from dataclasses import dataclass
from typing import List
from lifeblocks.models.block import Block


@dataclass
class BlockQueue:
    blocks: List[Block]
    total_multiplier: float = 1.0

    def __init__(self, initial_block: Block = None):
        self.blocks = []
        self.total_multiplier = 0
        if initial_block:
            self.add_block(initial_block)

    def add_block(self, block: Block):
        self.blocks.append(block)
        self.total_multiplier += block.length_multiplier

    def is_full(self):
        return self.total_multiplier >= 1.0

    def has_space_for(self, block: Block):
        return self.total_multiplier + block.length_multiplier <= 1.0


class BlockService:
    def __init__(self, session):
        self.session = session

    def add_block(
        self,
        name,
        weight=1,
        parent_name=None,
        max_interval_hours=None,
        length_multiplier=1.0,
        min_duration_minutes=None,
    ):
        parent_id = None
        if parent_name and parent_name != "None":
            parent = self.session.query(Block).filter_by(name=parent_name).first()
            if parent:
                parent_id = parent.id

        new_block = Block(
            name=name,
            weight=weight,
            parent_id=parent_id,
            max_interval_hours=max_interval_hours,
            length_multiplier=length_multiplier,
            min_duration_minutes=min_duration_minutes,
        )
        self.session.add(new_block)
        self.session.commit()
        return new_block

    def get_all_blocks(self):
        return self.session.query(Block).all()

    def get_root_blocks(self):
        return self.session.query(Block).filter_by(parent_id=None).all()

    def update_block(
        self,
        block_id,
        name=None,
        weight=None,
        parent_name=None,
        max_interval_hours=None,
        length_multiplier=None,
        min_duration_minutes=None,
    ):
        block = self.session.query(Block).get(block_id)
        if not block:
            return None

        if name:
            block.name = name
        if weight:
            block.weight = weight
        if parent_name is not None:
            parent_id = None
            if parent_name != "None":
                parent = self.session.query(Block).filter_by(name=parent_name).first()
                if parent:
                    parent_id = parent.id
            block.parent_id = parent_id
        if max_interval_hours is not None:
            block.max_interval_hours = (
                max_interval_hours if max_interval_hours >= 0 else None
            )
        if length_multiplier is not None:
            block.length_multiplier = length_multiplier
        if min_duration_minutes is not None:
            block.min_duration_minutes = min_duration_minutes

        self.session.commit()
        return block

    def delete_block(self, block_id):
        def delete_children(parent_id):
            children = self.session.query(Block).filter_by(parent_id=parent_id).all()
            for child in children:
                delete_children(child.id)
                self.session.delete(child)

        block = self.session.query(Block).get(block_id)
        if block:
            delete_children(block.id)
            self.session.delete(block)
            self.session.commit()
            return True
        return False

    def pick_block_queue(self):
        def get_overdue_blocks(blocks):
            """Return blocks that have exceeded their max interval"""
            now = datetime.now()
            return [
                block
                for block in blocks
                if (
                    block.max_interval_hours is not None
                    and block.last_picked is not None
                    and (now - block.last_picked).total_seconds() / 3600
                    > block.max_interval_hours
                )
            ]

        def calculate_weighted_blocks(blocks):
            """Calculate weights for non-overdue blocks"""
            now = datetime.now()
            weighted_blocks = []

            for block in blocks:
                # Skip blocks that have exceeded max interval
                if (
                    block.max_interval_hours is not None
                    and block.last_picked is not None
                    and (now - block.last_picked).total_seconds() / 3600
                    > block.max_interval_hours
                ):
                    continue

                base_weight = block.weight
                time_weight = (
                    (now - block.last_picked).days / 7 if block.last_picked else 2
                )
                total_weight = base_weight * (1 + time_weight)
                weighted_blocks.append((block, total_weight))

            return weighted_blocks

        def select_weighted_block(weighted_blocks):
            if not weighted_blocks:
                return None

            total_weight = sum(weight for _, weight in weighted_blocks)
            random_choice = random.uniform(0, total_weight)

            cumulative_weight = 0
            for block, weight in weighted_blocks:
                cumulative_weight += weight
                if cumulative_weight > random_choice:
                    return block

            return weighted_blocks[-1][0]

        def pick_block_queue_recursive(blocks):
            """Pick a block and create a queue, potentially with repeated blocks to fill time"""
            if not blocks:
                return None

            # First check for overdue blocks at this level
            overdue_blocks = get_overdue_blocks(blocks)
            if overdue_blocks:
                selected_block = random.choice(overdue_blocks)
            else:
                # Otherwise use weighted selection
                weighted_blocks = calculate_weighted_blocks(blocks)
                selected_block = select_weighted_block(weighted_blocks)

            if not selected_block:
                return None

            # Get children of the selected block
            children = (
                self.session.query(Block).filter_by(parent_id=selected_block.id).all()
            )

            if not children:
                # If no children, we've reached a leaf node - return it as a single-block queue
                queue = BlockQueue(selected_block)
                return queue

            # Pick from children and create a queue
            child_queue = pick_block_queue_recursive(children)
            if not child_queue:
                # If no valid child queue, return the current block
                queue = BlockQueue(selected_block)
                return queue

            # If the queue isn't full and we have a fractional block, keep picking more blocks
            while not child_queue.is_full():
                # Pick another child using the same weighted selection
                next_block = select_weighted_block(calculate_weighted_blocks(children))
                if next_block and next_block.length_multiplier < 1.0:
                    child_queue.add_block(next_block)
                else:
                    break  # Stop if we can't find a suitable block

            return child_queue

        # Start the recursive selection from root blocks
        root_blocks = self.get_root_blocks()
        return pick_block_queue_recursive(root_blocks)

    def initialize_default_categories(self, settings_service):
        # Check if this is first run using settings
        if settings_service.get_setting("first_run_complete") == "true":
            return

        default_categories = [
            ("Core Creative Projects", 4),
            ("Skill Development", 2),
            ("Infrastructure & Maintenance", 1),
            ("Experimental", 1.5),
            ("Human Condition", 1),
        ]

        # Add main categories
        for name, weight in default_categories:
            self.add_block(name=name, weight=weight)

        # Add Human Condition subcategories
        human_condition = next(
            p for p in self.get_all_blocks() if p.name == "Human Condition"
        )
        self.add_block(
            "Cooking", weight=1, parent_name="Human Condition", max_interval_hours=4
        )
        self.add_block(
            "Cleaning", weight=1, parent_name="Human Condition", max_interval_hours=24
        )
        # Mark first run as complete
        settings_service.set_setting("first_run_complete", "true")

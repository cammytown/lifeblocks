from datetime import datetime
import random
from lifeblocks.models.block import Block


class BlockService:
    def __init__(self, session):
        self.session = session

    def add_block(self, name, weight=1, parent_name=None, max_interval_hours=None):
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

    def pick_random_block(self):
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

        def pick_block_recursive(blocks):
            """Recursively pick a block from the hierarchy"""
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
                # If no children, we've reached a leaf node
                return selected_block

            # Recursively pick from children
            child_pick = pick_block_recursive(children)
            # Return the child if we found one, otherwise return the current block
            return child_pick if child_pick else selected_block

        # Start the recursive selection from root blocks
        root_blocks = self.get_root_blocks()
        return pick_block_recursive(root_blocks)

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

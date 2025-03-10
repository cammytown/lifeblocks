from datetime import datetime, timedelta
import random
from typing import List, Tuple, Optional
from lifeblocks.models.block import Block
from lifeblocks.models.block_queue import BlockQueue
from lifeblocks.models.timeblock import PickReason, TimeBlock, TimeBlockState


class BlockService:
    def __init__(self, session, settings_service):
        self.session = session
        self.settings_service = settings_service

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

    def get_all_active_blocks(self):
        """Get all blocks that are active."""
        return self.session.query(Block).filter_by(active=True).all()

    def get_active_root_blocks(self):
        """Get all root blocks that are active."""
        return self.session.query(Block).filter_by(parent_id=None, active=True).all()

    def update_block(
        self,
        block_id,
        name=None,
        weight=None,
        parent_name=None,
        max_interval_hours=None,
        length_multiplier=None,
        min_duration_minutes=None,
        active=None,
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
        if active is not None:
            block.active = active

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

    def get_all_leaf_blocks(self):
        """Get all blocks that have no children."""
        all_blocks = self.get_all_blocks()
        return [block for block in all_blocks if not any(b.parent_id == block.id for b in all_blocks)]

    def _has_active_parent_chain(self, block, all_blocks=None):
        """Check if all parents in a block's hierarchy are active."""
        if all_blocks is None:
            all_blocks = self.get_all_blocks()
            
        current_id = block.parent_id
        while current_id is not None:
            parent = next((b for b in all_blocks if b.id == current_id), None)
            if not parent or not parent.active:
                return False
            current_id = parent.parent_id
        return True
        
    def get_active_leaf_blocks(self):
        """Get all active blocks that have no children and whose parents are all active."""
        all_blocks = self.get_all_blocks()
        
        # First find all leaf blocks (blocks with no children)
        leaf_blocks = [block for block in all_blocks if not any(b.parent_id == block.id for b in all_blocks)]
        
        # Then filter for active leaf blocks with active parent chain
        return [block for block in leaf_blocks if block.active and self._has_active_parent_chain(block, all_blocks)]

    def calculate_accumulated_weight(self, block, time_weight_multiplier=1.0):
        """Calculate a block's weight including its parent's influence."""
        weight = block.weight
        current = block
        
        # Traverse up the parent chain, multiplying weights
        while current.parent_id is not None:
            parent = self.session.query(Block).get(current.parent_id)
            if not parent:
                break
            weight *= parent.weight
            current = parent
            
        # Apply time-based weight multiplier
        if time_weight_multiplier > 1.0:
            weight *= time_weight_multiplier
            
        return weight

    def _calculate_weighted_blocks(self, blocks: List[Block], include_parent_weights: bool = False) -> List[Tuple[Block, float]]:
        """Calculate weights for non-overdue blocks"""
        now = datetime.now()
        weighted_blocks = []

        
        # Check if debug mode is enabled
        debug_mode = self.settings_service.get_setting("debug_mode", "false") == "true"

        for block in blocks:
            # Skip blocks that have exceeded max interval
            if (
                block.max_interval_hours is not None
                and block.last_picked is not None
                and (now - block.last_picked).total_seconds() / 3600
                > block.max_interval_hours
            ):
                continue

            hours_until_double = float(self.settings_service.get_setting("hours_until_double_weight", "48"))
            time_multiplier = 1.0 / hours_until_double
            # For unpicked blocks, use time since creation instead of a fixed value
            hours_since_picked = (
                (now - block.last_picked).total_seconds() / 3600 if block.last_picked
                else (now - block.created_at).total_seconds() / 3600
            )
            time_weight = 1.0 + (hours_since_picked * time_multiplier)
            
            # Calculate weight including parent influence if requested
            total_weight = self.calculate_accumulated_weight(block, time_weight) if include_parent_weights else block.weight * time_weight
            weighted_blocks.append((block, total_weight))

            if debug_mode:
                base_weight = block.weight
                time_factor = f"(1 + {hours_since_picked:.1f}h * {time_multiplier:.4f})"
                if include_parent_weights:
                    print(f"Block: {block.name:<30} | Base Weight: {base_weight:<5} | Time Factor: {time_factor:<20} | Final Weight: {total_weight:.2f}")
                else:
                    print(f"Block: {block.name:<30} | Weight: {base_weight:<5} | Time Factor: {time_factor:<20} | Final Weight: {total_weight:.2f}")


        return weighted_blocks

    def _select_weighted_block(self, weighted_blocks: List[Tuple[Block, float]]) -> Optional[Block]:
        """Select a block using weighted random selection"""
        if not weighted_blocks:
            return None

        total_weight = sum(weight for _, weight in weighted_blocks)
        random_choice = random.uniform(0, total_weight)

        cumulative_weight = 0
        for block, weight in weighted_blocks:
            cumulative_weight += weight
            if cumulative_weight > random_choice:
                return block

        return weighted_blocks[-1][0] if weighted_blocks else None

    def _fill_fractional_queue(self, queue: BlockQueue, blocks: List[Block], overdue_blocks: Optional[List[Block]] = None) -> None:
        """Fill a queue with fractional blocks if enabled, prioritizing overdue blocks"""
        debug_mode = self.settings_service.get_setting("debug_mode", "false") == "true"
        should_fill_queues = self.settings_service.get_setting("fill_fractional_queues", "true") == "true"
        
        if debug_mode:
            print("\n=== Filling Fractional Queue ===")
            print(f"Fill queues enabled: {should_fill_queues}")
            print(f"Current queue length: {queue.total_multiplier}")
            
        if not should_fill_queues:
            return

        # First try to fill with overdue blocks if any were provided
        if overdue_blocks:
            remaining_overdue = [b for b in overdue_blocks if b not in queue.blocks and b.length_multiplier < 1.0]
            if debug_mode:
                print(f"Attempting to fill with {len(remaining_overdue)} remaining overdue blocks")
            
            while not queue.is_full() and remaining_overdue:
                next_block = random.choice(remaining_overdue)
                if debug_mode:
                    print(f"Trying overdue block: {next_block.name} (length_multiplier: {next_block.length_multiplier})")
                    print(f"Queue has space: {queue.has_space_for(next_block)}")
                
                if queue.has_space_for(next_block):
                    queue.add_block(next_block)
                    if debug_mode:
                        print(f"Added overdue block. New queue length: {queue.total_multiplier}")
                remaining_overdue.remove(next_block)

        # If queue still not full, fall back to weighted selection
        if debug_mode and not queue.is_full():
            print("\nAttempting to fill remaining space with weighted blocks")
            
        # Filter out blocks already in queue and non-fractional blocks
        available_blocks = [b for b in blocks if b not in queue.blocks and b.length_multiplier < 1.0]
        weighted_blocks = self._calculate_weighted_blocks(available_blocks, include_parent_weights=True)
        
        attempts = 0  # Add a counter to prevent infinite loops
        max_attempts = 10  # Maximum number of attempts to fill the queue
        
        while not queue.is_full() and attempts < max_attempts:
            attempts += 1
            if not weighted_blocks:
                if debug_mode:
                    print("No more available blocks to fill queue")
                break
                
            next_block = self._select_weighted_block(weighted_blocks)
            if not next_block:
                if debug_mode:
                    print("No block selected")
                break
                
            if debug_mode:
                print(f"Selected block: {next_block.name} (length_multiplier: {next_block.length_multiplier})")
                print(f"Queue has space: {queue.has_space_for(next_block)}")
            
            if queue.has_space_for(next_block):
                queue.add_block(next_block)
                if debug_mode:
                    print(f"Added block. New queue length: {queue.total_multiplier}")
                # Remove the added block from weighted_blocks
                weighted_blocks = [(b, w) for b, w in weighted_blocks if b != next_block]
            else:
                if debug_mode:
                    print("Block wouldn't fit in remaining space")
                break

    def _build_block_queue(self, blocks: List[Block]) -> Optional[BlockQueue]:
        """Build a queue from candidate blocks, respecting length multipliers."""
        debug_mode = self.settings_service.get_setting("debug_mode", "false") == "true"
        
        # Check for overdue blocks
        now = datetime.now()
        overdue_blocks = [
            block
            for block in blocks
            if (
                block.max_interval_hours is not None
                and block.last_picked is not None
                and (now - block.last_picked).total_seconds() / 3600
                > block.max_interval_hours
                and not self.was_recently_delayed(block)
            )
        ]

        if debug_mode:
            print("\n=== Building Block Queue ===")
            print(f"Found {len(overdue_blocks)} overdue blocks")

        # First try overdue blocks
        if overdue_blocks:
            selected_block = random.choice(overdue_blocks)
            if debug_mode:
                print(f"Selected overdue block: {selected_block.name} (length_multiplier: {selected_block.length_multiplier})")
            queue = BlockQueue(selected_block, pick_reason=PickReason.OVERDUE)
            self._fill_fractional_queue(queue, blocks, overdue_blocks)
            if debug_mode:
                print("Final queue composition:")
                for block in queue.blocks:
                    print(f"  - {block.name} (length_multiplier: {block.length_multiplier})")
                print(f"Total queue length: {queue.total_multiplier}")
            return queue

        # Calculate weighted blocks for selection
        weighted_blocks = self._calculate_weighted_blocks(blocks, include_parent_weights=True)
        
        # Filter weighted blocks by those that would fit
        fitting_weighted = [(b, w) for b, w in weighted_blocks if b.length_multiplier <= 1.0]
        if debug_mode:
            print(f"Found {len(fitting_weighted)} blocks that could fit as primary block")
        
        if not fitting_weighted:
            if debug_mode:
                print("No fitting blocks found")
            return None

        selected_block = self._select_weighted_block(fitting_weighted)
        if not selected_block:
            if debug_mode:
                print("Failed to select a block")
            return None

        if debug_mode:
            print(f"Selected primary block: {selected_block.name} (length_multiplier: {selected_block.length_multiplier})")

        queue = BlockQueue(selected_block, pick_reason=PickReason.NORMAL)
        self._fill_fractional_queue(queue, blocks, overdue_blocks)
        
        if debug_mode:
            print("Final queue composition:")
            for block in queue.blocks:
                print(f"  - {block.name} (length_multiplier: {block.length_multiplier})")
            print(f"Total queue length: {queue.total_multiplier}")
        
        return queue

    def pick_block_queue_leaf_based(self):
        """Pick a block queue by considering all leaf nodes together."""
        leaf_blocks = self.get_active_leaf_blocks()
        return self._build_block_queue(leaf_blocks)

    def pick_block_queue_hierarchical(self):
        """Pick a block queue using the hierarchical method."""
        def pick_block_queue_recursive(blocks):
            if not blocks:
                return None

            # Filter out inactive blocks
            active_blocks = [block for block in blocks if block.active]
            if not active_blocks:
                return None

            # Build queue at this level
            selected_queue = self._build_block_queue(active_blocks)
            if not selected_queue:
                return None
                
            selected_block = selected_queue.blocks[0]  # Get the primary block from the queue
            children = self.session.query(Block).filter_by(parent_id=selected_block.id, active=True).all()

            if not children:
                # If no children, return the queue we built
                return selected_queue

            # Try to pick from children
            child_queue = pick_block_queue_recursive(children)
            return child_queue if child_queue else selected_queue

        # Start the recursive selection from root blocks
        root_blocks = self.get_active_root_blocks()
        return pick_block_queue_recursive(root_blocks)

    def pick_block_queue(self):
        """Pick a block queue using either the hierarchical or leaf-based method."""
        use_leaf_based = self.settings_service.get_setting("use_leaf_based_selection", "true") == "true"
        if use_leaf_based:
            return self.pick_block_queue_leaf_based()
        else:
            return self.pick_block_queue_hierarchical()

    def initialize_default_categories(self):
        # Check if this is first run using settings
        if self.settings_service.get_setting("first_run_complete") == "true":
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
        self.settings_service.set_setting("first_run_complete", "true")

    def get_category_path(self, block_id: int) -> str:
        """Get the category path for a block, excluding the block itself."""
        block = self.session.query(Block).get(block_id)
        if not block:
            return ""

        path = []
        current = block

        # Traverse up the parent chain
        while current.parent_id is not None:
            parent = self.session.query(Block).get(current.parent_id)
            if not parent:
                break
            path.append(parent.name)
            current = parent

        # Return path from root to parent (excluding the block itself)
        return " → ".join(reversed(path)) if path else ""

    def create_single_block_queue(self, block_id):
        """Create a queue with just a single block."""
        block = self.session.query(Block).get(block_id)
        if not block:
            return None
        queue = BlockQueue(block)
        return queue

    def create_delayed_timeblock(self, block_id, delay_hours=None):
        """Create a TimeBlock entry to record that a block was delayed."""
        now = datetime.now()
        timeblock = TimeBlock(
            block_id=block_id,
            start_time=now,
            duration_minutes=0,
            state=TimeBlockState.DELAYED,
            delay_hours=delay_hours
        )
        self.session.add(timeblock)
        self.session.commit()
        return timeblock

    def was_recently_delayed(self, block: Block, hours: int = 4) -> bool:
        """Check if a block was delayed within the last n hours."""
        if not block:
            return False
            
        now = datetime.now()
        
        # Get the most recent delay for this block
        recent_delay = (
            self.session.query(TimeBlock)
            .filter(
                TimeBlock.block_id == block.id,
                TimeBlock.state == TimeBlockState.DELAYED
            )
            .order_by(TimeBlock.start_time.desc())
            .first()
        )
        
        if not recent_delay:
            return False
            
        # Use the delay_hours from the TimeBlock, or fall back to 4 hours
        delay_duration = recent_delay.delay_hours or 4
        cutoff = now - timedelta(hours=delay_duration)
        
        return recent_delay.start_time >= cutoff

    def toggle_block_active_status(self, block_id):
        """Toggle the active status of a block."""
        block = self.session.query(Block).get(block_id)
        if block:
            block.active = not block.active
            self.session.commit()
            return block
        return None

    def toggle_block_active_status_recursive(self, block_id):
        """Toggle the active status of a block and all its children."""
        block = self.session.query(Block).get(block_id)
        if not block:
            return None
            
        # Toggle the block's active status
        new_status = not block.active
        block.active = new_status
        
        # Recursively toggle all children
        def toggle_children(parent_id, status):
            children = self.session.query(Block).filter_by(parent_id=parent_id).all()
            for child in children:
                child.active = status
                toggle_children(child.id, status)
                
        toggle_children(block_id, new_status)
        self.session.commit()
        return block

    def set_block_active_status(self, block_id, active):
        """Set the active status of a block."""
        block = self.session.query(Block).get(block_id)
        if block:
            block.active = active
            self.session.commit()
            return block
        return None

import unittest
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lifeblocks.models.block import Base, Block
from lifeblocks.services.block_service import BlockService


class TestBlockPicking(unittest.TestCase):
    def setUp(self):
        # Create in-memory database for testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.block_service = BlockService(self.session)

    def tearDown(self):
        self.session.close()

    def test_weight_distribution(self):
        """Test if block selection follows the expected weight distribution"""
        # Create test blocks with different weights
        blocks = [("Block A", 1), ("Block B", 2), ("Block C", 3)]

        for name, weight in blocks:
            self.block_service.add_block(name, weight)

        # Perform many picks and count occurrences
        num_picks = 10000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            # These blocks should have default length_multiplier=1.0, so expect single block
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)
        total_weight = sum(weight for _, weight in blocks)

        # Check if the distribution roughly matches expected probabilities
        # Allow for 5% deviation from expected values
        for name, weight in blocks:
            expected_ratio = weight / total_weight
            actual_ratio = counts[name] / num_picks
            self.assertAlmostEqual(actual_ratio, expected_ratio, delta=0.05)

    def test_time_weight(self):
        """Test if time weight affects block selection"""
        # Create two blocks with equal base weights
        block_a = self.block_service.add_block("Block A", 1)
        block_b = self.block_service.add_block("Block B", 1)

        # Set Block A as picked recently, Block B as picked long ago
        block_a.last_picked = datetime.now()
        block_b.last_picked = datetime.now() - timedelta(days=14)
        self.session.commit()

        # Perform picks and verify Block B is selected more often
        num_picks = 1000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            # Expect single blocks as length_multiplier=1.0
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)
        # Block B should be picked more often due to time weight
        self.assertGreater(counts["Block B"], counts["Block A"])

    def test_hierarchical_selection(self):
        """Test parent-child block selection"""
        # Create parent blocks with different weights
        parent_a = self.block_service.add_block("Parent A", 1)
        parent_b = self.block_service.add_block("Parent B", 2)

        # Create children for Parent A
        self.block_service.add_block("Child A1", 1, "Parent A")
        self.block_service.add_block("Child A2", 2, "Parent A")

        # Create children for Parent B
        self.block_service.add_block("Child B1", 1, "Parent B")
        self.block_service.add_block("Child B2", 1, "Parent B")

        # Perform many picks
        num_picks = 1000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            # Expect single blocks as length_multiplier=1.0
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)

        # Verify that Parent B's children are selected more often than Parent A's
        parent_a_children_picks = counts["Child A1"] + counts["Child A2"]
        parent_b_children_picks = counts["Child B1"] + counts["Child B2"]

        # Allow for some statistical variation but Parent B's children should be picked more
        self.assertGreater(parent_b_children_picks, parent_a_children_picks)

    def test_max_interval(self):
        """Test if blocks with max intervals are respected"""
        # Create blocks with different max intervals
        block_a = self.block_service.add_block(
            "Block A", 1, max_interval_hours=2
        )  # 2 hours
        block_b = self.block_service.add_block(
            "Block B", 1, max_interval_hours=24
        )  # 1 day
        block_c = self.block_service.add_block("Block C", 1)  # No max interval

        # Set last picked times
        now = datetime.now()
        block_a.last_picked = now - timedelta(hours=3)  # Overdue
        block_b.last_picked = now - timedelta(hours=12)  # Not overdue
        block_c.last_picked = now - timedelta(hours=48)  # No max interval
        self.session.commit()

        # Test multiple picks to ensure overdue block is prioritized
        num_picks = 100
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            # Expect single blocks as length_multiplier=1.0
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)

        # Block A should be picked more often as it's overdue
        self.assertGreater(counts["Block A"], counts["Block B"])
        self.assertGreater(counts["Block A"], counts["Block C"])

    def test_fractional_block_queue(self):
        """Test that fractional blocks are properly queued"""
        # Create a parent block
        parent = self.block_service.add_block("Parent", 1)

        # Create child blocks with fractional lengths
        child_a = self.block_service.add_block(
            "Child A", 1, "Parent", length_multiplier=0.3
        )
        child_b = self.block_service.add_block(
            "Child B", 1, "Parent", length_multiplier=0.4
        )
        child_c = self.block_service.add_block(
            "Child C", 1, "Parent", length_multiplier=0.5
        )

        # Test multiple picks to analyze queue behavior
        num_picks = 100
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()

            # Queue should have multiple blocks
            self.assertGreater(len(block_queue.blocks), 1)

            # Total multiplier should be >= 1.0
            self.assertGreaterEqual(block_queue.total_multiplier, 1.0)

            # All blocks in queue should be children of the same parent
            parent_ids = {block.parent_id for block in block_queue.blocks}
            self.assertEqual(len(parent_ids), 1)

            # All blocks should be from our test set
            for block in block_queue.blocks:
                self.assertIn(block.name, ["Child A", "Child B", "Child C"])

    def test_single_block_with_length_one(self):
        """Test that blocks with length_multiplier=1.0 are returned as single-block queues"""
        block = self.block_service.add_block("Block", 1, length_multiplier=1.0)

        block_queue = self.block_service.pick_block_queue()
        self.assertEqual(len(block_queue.blocks), 1)
        self.assertEqual(block_queue.blocks[0].name, "Block")
        self.assertEqual(block_queue.total_multiplier, 1.0)


if __name__ == "__main__":
    unittest.main()

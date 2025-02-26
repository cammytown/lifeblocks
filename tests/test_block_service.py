import unittest
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lifeblocks.models.block import Base, Block
from lifeblocks.services.block_service import BlockService
from lifeblocks.services.settings_service import SettingsService

class TestBlockPicking(unittest.TestCase):
    def setUp(self):
        # Create in-memory database for testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.settings_service = SettingsService(self.session)
        self.block_service = BlockService(self.session, self.settings_service)
        
        # Default to hierarchical selection
        self.settings_service.set_setting("use_leaf_based_selection", "false")

    def tearDown(self):
        self.session.close()

    def test_weight_distribution_hierarchical(self):
        """Test if block selection follows the expected weight distribution in hierarchical mode"""
        self.settings_service.set_setting("use_leaf_based_selection", "false")
        
        # Create test blocks with different weights
        blocks = [("Block A", 1), ("Block B", 2), ("Block C", 3)]

        for name, weight in blocks:
            self.block_service.add_block(name, weight)

        # Perform many picks and count occurrences
        num_picks = 10000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
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

    def test_weight_distribution_leaf_based(self):
        """Test if block selection follows the expected weight distribution in leaf-based mode"""
        self.settings_service.set_setting("use_leaf_based_selection", "true")
        
        # Create a hierarchy of blocks with different weights
        parent_a = self.block_service.add_block("Parent A", 2)  # weight 2
        parent_b = self.block_service.add_block("Parent B", 3)  # weight 3
        
        # Create leaf nodes with weights
        leaf_a1 = self.block_service.add_block("Leaf A1", 2, "Parent A")  # accumulated weight: 2 * 2 = 4
        leaf_a2 = self.block_service.add_block("Leaf A2", 1, "Parent A")  # accumulated weight: 2 * 1 = 2
        leaf_b1 = self.block_service.add_block("Leaf B1", 1, "Parent B")  # accumulated weight: 3 * 1 = 3
        
        # Perform many picks and count occurrences
        num_picks = 10000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)
        total_weight = 9  # sum of accumulated weights: 4 + 2 + 3 = 9

        # Check distribution matches accumulated weights
        expected_ratios = {
            "Leaf A1": 4/9,  # weight 4 out of 9
            "Leaf A2": 2/9,  # weight 2 out of 9
            "Leaf B1": 3/9,  # weight 3 out of 9
        }
        
        for name, expected_ratio in expected_ratios.items():
            actual_ratio = counts[name] / num_picks
            self.assertAlmostEqual(actual_ratio, expected_ratio, delta=0.05)
            
        # Verify only leaf nodes were picked
        self.assertEqual(counts["Parent A"], 0)
        self.assertEqual(counts["Parent B"], 0)

    def test_time_weight(self):
        """Test if time weight affects block selection"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
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
                self.assertEqual(len(block_queue.blocks), 1)
                picks.append(block_queue.blocks[0].name)

            counts = Counter(picks)
            # Block B should be picked more often due to time weight
            self.assertGreater(counts["Block B"], counts["Block A"])
            
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()

    def test_hierarchical_selection(self):
        """Test parent-child block selection in hierarchical mode"""
        self.settings_service.set_setting("use_leaf_based_selection", "false")
        
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
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)

        counts = Counter(picks)

        # Verify that Parent B's children are selected more often than Parent A's
        parent_a_children_picks = counts["Child A1"] + counts["Child A2"]
        parent_b_children_picks = counts["Child B1"] + counts["Child B2"]

        # Allow for some statistical variation but Parent B's children should be picked more
        self.assertGreater(parent_b_children_picks, parent_a_children_picks)

    def test_leaf_based_selection(self):
        """Test that leaf-based selection properly accumulates weights through the hierarchy"""
        self.settings_service.set_setting("use_leaf_based_selection", "true")
        
        # Create a deep hierarchy with known accumulated weights
        root = self.block_service.add_block("Root", 2)  # weight 2
        branch_a = self.block_service.add_block("Branch A", 3, "Root")  # accumulated: 2 * 3 = 6
        branch_b = self.block_service.add_block("Branch B", 1, "Root")  # accumulated: 2 * 1 = 2
        
        # Create leaf nodes
        leaf_a = self.block_service.add_block("Leaf A", 2, "Branch A")  # accumulated: 2 * 3 * 2 = 12
        leaf_b = self.block_service.add_block("Leaf B", 3, "Branch B")  # accumulated: 2 * 1 * 3 = 6
        
        # Perform many picks
        num_picks = 10000
        picks = []
        for _ in range(num_picks):
            block_queue = self.block_service.pick_block_queue()
            self.assertEqual(len(block_queue.blocks), 1)
            picks.append(block_queue.blocks[0].name)
            
        counts = Counter(picks)
        
        # Verify only leaf nodes were picked
        self.assertEqual(counts["Root"], 0)
        self.assertEqual(counts["Branch A"], 0)
        self.assertEqual(counts["Branch B"], 0)
        
        # Check distribution matches accumulated weights
        total_weight = 18  # 12 + 6
        self.assertAlmostEqual(counts["Leaf A"] / num_picks, 12/18, delta=0.05)  # Should be picked ~66.7% of the time
        self.assertAlmostEqual(counts["Leaf B"] / num_picks, 6/18, delta=0.05)   # Should be picked ~33.3% of the time

    def test_max_interval(self):
        """Test if blocks with max intervals are respected in both modes"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
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
                self.assertEqual(len(block_queue.blocks), 1)
                picks.append(block_queue.blocks[0].name)

            counts = Counter(picks)

            # Block A should be picked more often as it's overdue
            self.assertGreater(counts["Block A"], counts["Block B"])
            self.assertGreater(counts["Block A"], counts["Block C"])
            
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()

    def test_fractional_block_queue(self):
        """Test that fractional blocks are properly queued in both modes"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
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
                    
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()

    def test_single_block_with_length_one(self):
        """Test that blocks with length_multiplier=1.0 are returned as single-block queues"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
            block = self.block_service.add_block("Block", 1, length_multiplier=1.0)

            block_queue = self.block_service.pick_block_queue()
            self.assertEqual(len(block_queue.blocks), 1)
            self.assertEqual(block_queue.blocks[0].name, "Block")
            self.assertEqual(block_queue.total_multiplier, 1.0)
            
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()
            
    def test_inactive_blocks_excluded(self):
        """Test that inactive blocks are excluded from selection"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
            # Create active and inactive blocks
            active_block = self.block_service.add_block("Active Block", 1)
            inactive_block = self.block_service.add_block("Inactive Block", 10)  # Higher weight
            
            # Set inactive block to inactive
            inactive_block.active = False
            self.session.commit()
            
            # Perform many picks to ensure inactive block is never selected
            num_picks = 100
            for _ in range(num_picks):
                block_queue = self.block_service.pick_block_queue()
                self.assertEqual(len(block_queue.blocks), 1)
                self.assertEqual(block_queue.blocks[0].name, "Active Block")
                
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()
            
    def test_inactive_parent_blocks(self):
        """Test that children of inactive parent blocks are excluded from selection"""
        for mode in ["true", "false"]:  # Test both selection modes
            self.settings_service.set_setting("use_leaf_based_selection", mode)
            
            # Create active parent with active children
            active_parent = self.block_service.add_block("Active Parent", 1)
            active_child = self.block_service.add_block("Active Child", 1, "Active Parent")
            
            # Create inactive parent with active children
            inactive_parent = self.block_service.add_block("Inactive Parent", 10)  # Higher weight
            inactive_child = self.block_service.add_block("Child of Inactive", 1, "Inactive Parent")
            
            # Set inactive parent to inactive
            inactive_parent.active = False
            self.session.commit()
            
            # Perform many picks to ensure children of inactive parents are never selected
            num_picks = 100
            picks = []
            for _ in range(num_picks):
                block_queue = self.block_service.pick_block_queue()
                self.assertEqual(len(block_queue.blocks), 1)
                picks.append(block_queue.blocks[0].name)
                
            # Verify only active blocks were picked
            self.assertIn("Active Child", picks)
            self.assertNotIn("Child of Inactive", picks)
            self.assertNotIn("Inactive Parent", picks)
            
            # Clean up for next iteration
            self.session.query(Block).delete()
            self.session.commit()
            
    def test_recursive_toggle_active(self):
        """Test that toggling active status recursively affects all children"""
        # Create a hierarchy of blocks
        parent = self.block_service.add_block("Parent", 1)
        child1 = self.block_service.add_block("Child 1", 1, "Parent")
        child2 = self.block_service.add_block("Child 2", 1, "Parent")
        grandchild = self.block_service.add_block("Grandchild", 1, "Child 1")
        
        # All blocks should be active by default
        blocks = self.session.query(Block).all()
        for block in blocks:
            self.assertTrue(block.active)
            
        # Toggle parent to inactive recursively
        self.block_service.toggle_block_active_status_recursive(parent.id)
        
        # All blocks should now be inactive
        blocks = self.session.query(Block).all()
        for block in blocks:
            self.assertFalse(block.active)
            
        # Toggle parent back to active recursively
        self.block_service.toggle_block_active_status_recursive(parent.id)
        
        # All blocks should now be active again
        blocks = self.session.query(Block).all()
        for block in blocks:
            self.assertTrue(block.active)


if __name__ == "__main__":
    unittest.main()

from tkinter import ttk
import tkinter as tk
from datetime import datetime, timedelta
from lifeblocks.models import TimeBlock, Block
from lifeblocks.models.timeblock import TimeBlockState
import tkinter.messagebox as messagebox
from sqlalchemy import tuple_


class HistoryFrame(ttk.Frame):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session
        self.setup_ui()

        # Set minimum height
        self.grid_propagate(False)
        self.configure(height=300)  # Minimum height of 300px

    def setup_ui(self):
        # Main container with padding
        self.configure(style="Card.TFrame", padding="20")

        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)

        # Header label
        ttk.Label(header_frame, text="History", font=("Helvetica", 16, "bold")).pack(
            side="left"
        )

        # Filter frame
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side="right")

        # Time filter
        ttk.Label(filter_frame, text="Time:").pack(side="left", padx=(0, 10))
        self.filter_var = tk.StringVar(value="Today")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"],
            state="readonly",
            width=15,
        )
        filter_combo.pack(side="left", padx=(0, 20))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_history())

        # State filter
        ttk.Label(filter_frame, text="State:").pack(side="left", padx=(0, 10))
        self.state_var = tk.StringVar(value="Current & Completed")
        excluded_states = [TimeBlockState.ABANDONED, TimeBlockState.EXPIRED, TimeBlockState.CANCELLED_ON_COMPLETE]
        state_values = ["Current & Completed", "All States"] + [state.value for state in TimeBlockState]
        state_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.state_var,
            values=state_values,
            state="readonly",
            width=15,
        )
        state_combo.pack(side="left", padx=(0, 20))
        state_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_history())

        # Delete button
        delete_button = ttk.Button(
            filter_frame,
            text="Delete Selected",
            style="Secondary.TButton",
            command=self.delete_selected,
        )
        delete_button.pack(side="left")

        # Tree view
        self.tree = ttk.Treeview(
            self,
            columns=(
                "block",
                "time",
                "duration",
                "paused",
                "resistance",
                "satisfaction",
                "notes",
                "state",
                "id",
            ),
            style="Custom.Treeview",
        )
        # Set column headers with alignment
        self.tree.heading("block", text="Block", anchor="w")
        self.tree.heading("time", text="Time", anchor="w")
        self.tree.heading("duration", text="Duration", anchor="w")
        self.tree.heading("paused", text="Paused", anchor="w")
        self.tree.heading("resistance", text="Resistance", anchor="w")
        self.tree.heading("satisfaction", text="Satisfaction", anchor="w")
        self.tree.heading("notes", text="Notes", anchor="w")
        self.tree.heading("state", text="State", anchor="w")

        # Set column properties with alignment
        self.tree.column("block", width=150, anchor="w")
        self.tree.column("time", width=150, anchor="w")
        self.tree.column("duration", width=100, anchor="w")
        self.tree.column("paused", width=100, anchor="w")
        self.tree.column("resistance", width=100, anchor="w")
        self.tree.column("satisfaction", width=100, anchor="w")
        self.tree.column("notes", width=200, anchor="w")
        self.tree.column("state", width=100, anchor="w")
        self.tree.column("id", width=0, stretch=False)  # Hidden column

        # Hide the id column
        self.tree["show"] = "headings"

        # Grid the tree with proper expansion
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5)

        # Scrollbar that only appears when needed
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")

        # Configure the tree to control scrollbar visibility
        def on_tree_configure(event):
            tree = event.widget
            if tree.yview() != (0.0, 1.0):  # Check if all items are visible
                scrollbar.grid()
            else:
                scrollbar.grid_remove()

        self.tree.configure(
            yscrollcommand=lambda first, last: self._update_scrollbar(
                scrollbar, first, last
            )
        )
        self.tree.bind("<Configure>", on_tree_configure)

        self.refresh_history()

    def _update_scrollbar(self, scrollbar, first, last):
        scrollbar.set(first, last)
        if float(first) <= 0 and float(last) >= 1:
            scrollbar.grid_remove()
        else:
            scrollbar.grid()

    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        blocks = self._get_filtered_blocks()
        row_count = 0

        for block in blocks:
            tag = "evenrow" if row_count % 2 == 0 else "oddrow"

            # Convert resistance level to lightning bolts (repeated based on level)
            resistance_text = (
                "⚡" * block.resistance_level if block.resistance_level else "-"
            )

            # Convert satisfaction level to stars (repeated based on level)
            satisfaction_text = (
                "★" * block.satisfaction_level if block.satisfaction_level else "-"
            )

            pause_text = (
                f"{block.pause_duration_minutes:.1f} min"
                if block.pause_duration_minutes > 0
                else "-"
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    block.block.name,
                    block.start_time.strftime("%Y-%m-%d %H:%M"),
                    f"{block.duration_minutes:.1f} min",
                    pause_text,
                    resistance_text,
                    satisfaction_text,
                    block.notes or "",
                    block.state.value if block.state else "-",
                    block.id,
                ),
                tags=(tag,),
            )
            row_count += 1

    def _get_filtered_blocks(self):
        filter_value = self.filter_var.get()
        state_value = self.state_var.get()
        now = datetime.now()

        if filter_value == "Today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_value == "Yesterday":
            start_date = (now - timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_value == "Last 7 Days":
            start_date = now - timedelta(days=7)
        elif filter_value == "Last 30 Days":
            start_date = now - timedelta(days=30)
        else:  # All Time
            start_date = datetime.min

        query = (
            self.session.query(TimeBlock)
            .join(Block)
            .filter(TimeBlock.deleted.is_(False))
        )

        # Add state filter
        if state_value == "Current & Completed":
            excluded_states = [
                TimeBlockState.ABANDONED,
                TimeBlockState.EXPIRED,
                TimeBlockState.CANCELLED_ON_COMPLETE,
                TimeBlockState.RESTARTED,
            ]
            query = query.filter(~TimeBlock.state.in_(excluded_states))
        elif state_value != "All States":
            query = query.filter(TimeBlock.state == TimeBlockState(state_value))

        if filter_value == "Yesterday":
            query = query.filter(
                TimeBlock.start_time >= start_date, TimeBlock.start_time < end_date
            )
        else:
            query = query.filter(TimeBlock.start_time >= start_date)

        return query.order_by(TimeBlock.start_time.desc()).all()

    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Warning", "Please select at least one item to delete!"
            )
            return

        item_count = len(selected_items)
        confirm_message = (
            "Are you sure you want to delete this history item?"
            if item_count == 1
            else f"Are you sure you want to delete these {item_count} history items?"
        )

        if not messagebox.askyesno("Confirm Delete", confirm_message):
            return

        try:
            # Get the index of the ID column
            columns = self.tree["columns"]
            id_column_index = columns.index("id")

            # Store the timeblock IDs
            timeblock_ids = []
            for item_id in selected_items:
                item = self.tree.item(item_id)
                timeblock_id = item["values"][id_column_index]
                timeblock_ids.append(timeblock_id)

            # Fetch and update the timeblocks
            timeblocks = (
                self.session.query(TimeBlock)
                .filter(TimeBlock.id.in_(timeblock_ids))
                .all()
            )

            # Mark all matched timeblocks as deleted
            now = datetime.now()
            for timeblock in timeblocks:
                timeblock.deleted = True
                timeblock.deleted_at = now
                
                # Update the block's last_picked to the most recent non-deleted timeblock
                latest_timeblock = (
                    self.session.query(TimeBlock)
                    .filter(
                        TimeBlock.block_id == timeblock.block_id,
                        TimeBlock.deleted.is_(False),
                        TimeBlock.id != timeblock.id
                    )
                    .order_by(TimeBlock.start_time.desc())
                    .first()
                )
                
                timeblock.block.last_picked = latest_timeblock.start_time if latest_timeblock else None

            self.session.commit()
            self.refresh_history()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", f"Failed to delete items: {str(e)}")

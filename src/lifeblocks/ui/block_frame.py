import tkinter as tk
from tkinter import ttk, messagebox
from .dialogs.edit_block_dialogue import EditBlockDialog
from .dialogs.add_block_dialogue import AddBlockDialog


class BlockFrame(ttk.Frame):
    def __init__(self, parent, block_service):
        super().__init__(parent)
        self.block_service = block_service
        self.setup_ui()

        # Set minimum height
        self.grid_propagate(False)
        self.configure(height=300)  # Minimum height of 300px

    def setup_ui(self):
        # Main container with padding
        self.configure(style="Card.TFrame", padding="20")

        # Configure grid weights for the frame itself
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        ttk.Label(header_frame, text="Blocks", font=("Helvetica", 16, "bold")).pack(
            side="left"
        )
        add_button = ttk.Button(
            header_frame,
            text="Add Block",
            style="Accent.TButton",
            command=self.show_add_dialog,
        )
        add_button.pack(side="right")

        # Block Tree with custom style
        self.tree = ttk.Treeview(
            self,
            columns=(
                "weight",
                "max_interval",
                "length_mult",
                "min_duration",
                "last_picked",
            ),
            style="Custom.Treeview",
        )
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("weight", text="Weight")
        self.tree.heading("max_interval", text="Max Interval")
        self.tree.heading("length_mult", text="Length Mult")
        self.tree.heading("min_duration", text="Min Duration")
        self.tree.heading("last_picked", text="Last Picked")
        self.tree.column("#0", anchor="w", minwidth=200)
        self.tree.column("weight", width=70, anchor="center")
        self.tree.column("max_interval", width=100, anchor="center")
        self.tree.column("length_mult", width=100, anchor="center")
        self.tree.column("min_duration", width=100, anchor="center")
        self.tree.column("last_picked", width=150, anchor="center")

        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=40)

        self.tree.grid(row=1, column=0, sticky="nsew")

        # Scrollbar with dynamic visibility
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")

        def on_tree_configure(event):
            tree = event.widget
            if tree.yview() != (0.0, 1.0):
                scrollbar.grid()
            else:
                scrollbar.grid_remove()

        def update_scrollbar(first, last):
            scrollbar.set(first, last)
            if float(first) <= 0 and float(last) >= 1:
                scrollbar.grid_remove()
            else:
                scrollbar.grid()

        self.tree.configure(yscrollcommand=update_scrollbar)
        self.tree.bind("<Configure>", on_tree_configure)
        self.tree.bind("<Double-1>", lambda e: self.edit_block())

        # Edit/Delete buttons in a frame at the bottom
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="e")

        ttk.Button(
            button_frame,
            text="Edit",
            command=self.edit_block,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame,
            text="Delete",
            command=self.delete_block,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT, padx=5)

        self.refresh_blocks()

    def show_add_dialog(self):
        selected = self.tree.selection()
        selected_block_name = None
        if selected:
            block_id = int(selected[0])
            block = next(
                (b for b in self.block_service.get_all_blocks() if b.id == block_id),
                None,
            )
            if block:
                selected_block_name = block.name
        dialog = AddBlockDialog(self, self.block_service, selected_block_name)
        if dialog.result:
            self.refresh_blocks()

    def refresh_blocks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        blocks = self.block_service.get_all_blocks()
        row_count = 0

        # First add root blocks
        for block in blocks:
            if block.parent_id is None:
                tag = "evenrow" if row_count % 2 == 0 else "oddrow"
                last_picked = (
                    block.last_picked.strftime("%Y-%m-%d %H:%M")
                    if block.last_picked
                    else "Never"
                )
                max_interval = (
                    f"{block.max_interval_hours}h"
                    if block.max_interval_hours is not None
                    else "-"
                )
                min_duration = (
                    f"{block.min_duration_minutes}m"
                    if block.min_duration_minutes is not None
                    else "-"
                )
                self.tree.insert(
                    "",
                    "end",
                    str(block.id),
                    text=block.name,
                    values=(
                        block.weight,
                        max_interval,
                        f"{block.length_multiplier:.2f}x",
                        min_duration,
                        last_picked,
                    ),
                    tags=(tag,),
                )
                row_count += 1

        # Then add child blocks
        for block in blocks:
            if block.parent_id is not None:
                tag = "evenrow" if row_count % 2 == 0 else "oddrow"
                last_picked = (
                    block.last_picked.strftime("%Y-%m-%d %H:%M")
                    if block.last_picked
                    else "Never"
                )
                max_interval = (
                    f"{block.max_interval_hours}h"
                    if block.max_interval_hours is not None
                    else "-"
                )
                min_duration = (
                    f"{block.min_duration_minutes}m"
                    if block.min_duration_minutes is not None
                    else "-"
                )
                self.tree.insert(
                    str(block.parent_id),
                    "end",
                    str(block.id),
                    text=block.name,
                    values=(
                        block.weight,
                        max_interval,
                        f"{block.length_multiplier:.2f}x",
                        min_duration,
                        last_picked,
                    ),
                    tags=(tag,),
                )
                row_count += 1

        # Expand all items
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def edit_block(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a block to edit!")
            return

        block_id = int(selected[0])
        dialog = EditBlockDialog(self, self.block_service, block_id)
        if dialog.result:
            self.refresh_blocks()

    def delete_block(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a block to delete!")
            return

        if messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this block and all its children?",
        ):
            block_id = int(selected[0])
            self.block_service.delete_block(block_id)
            self.refresh_blocks()

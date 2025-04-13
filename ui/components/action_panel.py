"""
Action panel component.
"""
import tkinter as tk
from tkinter import ttk

from utils.theme import AppTheme

class ActionPanel(ttk.Frame):
    """Panel containing action buttons and controls."""
    
    def __init__(self, parent, on_mark_question=None, on_mark_answer=None, 
                 on_mark_ignore=None, on_merge_up=None, on_set_expected_count=None,
                 on_exit=None, on_undo=None, on_redo=None):
        """
        Initialize the action panel.
        
        Args:
            parent: Parent widget
            on_mark_question: Callback for marking as question
            on_mark_answer: Callback for marking as answer
            on_mark_ignore: Callback for marking as ignore
            on_merge_up: Callback for merging into previous answer
            on_set_expected_count: Callback for setting expected count
            on_exit: Callback for exit button
            on_undo: Callback for undo button
            on_redo: Callback for redo button
        """
        super().__init__(parent, style='TFrame')
        
        self.on_mark_question = on_mark_question
        self.on_mark_answer = on_mark_answer
        self.on_mark_ignore = on_mark_ignore
        self.on_merge_up = on_merge_up
        self.on_set_expected_count = on_set_expected_count
        self.on_exit = on_exit
        self.on_undo = on_undo
        self.on_redo = on_redo
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # CRITICAL SIMPLIFICATION - remove scrolling and use simpler layout
        # Configure panel for proper resizing
        self.pack_propagate(False)  # Don't shrink the frame to fit its contents
        
        # Title header
        header_frame = ttk.Frame(self, style='Header.TFrame')
        header_frame.pack(fill=tk.X)
        
        header_label = ttk.Label(
            header_frame,
            text="Actions for Selected",
            style='Header.TLabel',
            font=AppTheme.FONTS['title'],
            padding=(10, 5)
        )
        header_label.pack(anchor="w", fill=tk.X)
        
        # Main content area - simple frame with padding
        content_frame = ttk.Frame(self, style='TFrame', padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # PRIMARY ACTION BUTTONS
        # Question button
        self.btn_question = ttk.Button(
            content_frame,
            text="Mark as QUESTION",
            command=self._on_mark_question,
            style='Action.TButton',
            width=20
        )
        self.btn_question.pack(pady=(0, 5), fill=tk.X)
        
        # Answer button
        self.btn_answer = ttk.Button(
            content_frame,
            text="Mark as ANSWER",
            command=self._on_mark_answer,
            style='Action.TButton',
            width=20
        )
        self.btn_answer.pack(pady=5, fill=tk.X)
        
        # Ignore button
        self.btn_ignore = ttk.Button(
            content_frame,
            text="Mark as IGNORE",
            command=self._on_mark_ignore,
            style='Action.TButton',
            width=20
        )
        self.btn_ignore.pack(pady=5, fill=tk.X)
        
        # Separator
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Merge button
        self.btn_merge_up = ttk.Button(
            content_frame,
            text="Add to Previous Answer",
            command=self._on_merge_up,
            style='Action.TButton',
            width=20
        )
        self.btn_merge_up.pack(pady=5, fill=tk.X)
        
        # Tooltip text
        tooltip = ttk.Label(
            content_frame,
            text="(For multi-paragraph answers)",
            foreground=AppTheme.COLORS['text_secondary'],
            font=("Segoe UI" if AppTheme.FONTS['normal'] is None else AppTheme.FONTS['normal'][0], 8)
        )
        tooltip.pack(pady=(0, 10))
        
        # Separator
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Undo/Redo in a row
        undo_frame = ttk.Frame(content_frame)
        undo_frame.pack(fill=tk.X, pady=5)
        undo_frame.columnconfigure(0, weight=1)
        undo_frame.columnconfigure(1, weight=1)
        
        self.btn_undo = ttk.Button(
            undo_frame,
            text="↩ Undo",
            command=self._on_undo,
            style='TButton'
        )
        self.btn_undo.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        
        self.btn_redo = ttk.Button(
            undo_frame,
            text="Redo ↪",
            command=self._on_redo,
            style='TButton'
        )
        self.btn_redo.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        
        # Separator
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Expected count
        count_label = ttk.Label(
            content_frame,
            text="Expected # of Questions:",
            font=AppTheme.FONTS['bold']
        )
        count_label.pack(anchor="w", pady=(5, 3))
        
        count_frame = ttk.Frame(content_frame)
        count_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.question_count_var = tk.StringVar(value="0")
        self.count_entry = ttk.Entry(
            count_frame,
            textvariable=self.question_count_var,
            width=8,
            justify=tk.CENTER
        )
        self.count_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        set_count_btn = ttk.Button(
            count_frame,
            text="Set",
            command=self._on_set_expected_count,
            style='TButton',
            width=8
        )
        set_count_btn.pack(side=tk.RIGHT)
        
        # Statistics
        stats_label = ttk.Label(
            content_frame,
            text="Current Stats:",
            font=AppTheme.FONTS['bold']
        )
        stats_label.pack(anchor="w", pady=(10, 3))
        
        self.stats_label = ttk.Label(
            content_frame,
            text="Questions: 0 / 0"
        )
        self.stats_label.pack(anchor="w", pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            content_frame,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Training status 
        self.training_frame = ttk.Frame(content_frame)
        self.training_frame.pack(fill=tk.X, pady=5)
        
        self.training_status_var = tk.StringVar(value="")
        self.training_status = ttk.Label(
            self.training_frame,
            textvariable=self.training_status_var,
            foreground=AppTheme.COLORS['accent'],
            wraplength=220
        )
        self.training_status.pack(fill=tk.X)
        
        # Initially hide training status
        self.training_frame.pack_forget()
        
        # Exit button - at the bottom
        exit_frame = ttk.Frame(content_frame)
        exit_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        exit_btn = ttk.Button(
            exit_frame,
            text="Exit Application",
            command=self._on_exit,
            style='Danger.TButton'
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # Initially disable action buttons
        self._update_button_states(False)
        
        # Initially disable undo/redo buttons
        self.update_undo_redo_state(False, False)
    
    def _update_button_states(self, enabled):
        """
        Update button states based on selection.
        
        Args:
            enabled: Whether buttons should be enabled
        """
        state = "normal" if enabled else "disabled"
        
        self.btn_question.config(state=state)
        self.btn_answer.config(state=state)
        self.btn_ignore.config(state=state)
        self.btn_merge_up.config(state=state)
    
    def update_selection_state(self, has_selection):
        """
        Update UI based on whether there's a selection.
        
        Args:
            has_selection: Whether there's a selection
        """
        self._update_button_states(has_selection)
    
    def update_undo_redo_state(self, can_undo, can_redo):
        """
        Update undo/redo button states.
        
        Args:
            can_undo: Whether undo is available
            can_redo: Whether redo is available
        """
        self.btn_undo.config(state="normal" if can_undo else "disabled")
        self.btn_redo.config(state="normal" if can_redo else "disabled")
    
    def update_progress(self, question_count, expected_count):
        """
        Update progress display.
        
        Args:
            question_count: Current question count
            expected_count: Expected question count
        """
        # Update progress bar
        if expected_count > 0:
            progress = (question_count / expected_count) * 100
            self.progress_var.set(progress)
        else:
            self.progress_var.set(0)
        
        # Determine color based on closeness to expected count
        if expected_count > 0:
            if question_count == expected_count:
                color = AppTheme.COLORS['success']
            elif abs(question_count - expected_count) <= max(2, expected_count * 0.1):  # Within 10% or 2 questions
                color = AppTheme.COLORS['warning']
            else:
                color = AppTheme.COLORS['danger']
        else:
            color = AppTheme.COLORS['text']
        
        # Update stats text
        status = f"Questions: {question_count} / {expected_count}"
        self.stats_label.config(text=status, foreground=color)
    
    def update_training_status(self, status_text=None):
        """
        Update the training status display.
        
        Args:
            status_text: Training status text to display (None to hide)
        """
        if status_text:
            self.training_status_var.set(status_text)
            # Ensure the training frame is visible
            if not self.training_frame.winfo_viewable():
                self.training_frame.pack(fill=tk.X, pady=5)
            self.update_idletasks()  # Force update
        else:
            # Hide the training frame
            self.training_frame.pack_forget()
            self.update_idletasks()  # Force update
    
    def set_expected_count(self, count):
        """
        Set the expected question count.
        
        Args:
            count: Expected question count
        """
        self.question_count_var.set(str(count))
    
    def get_expected_count(self):
        """
        Get the expected question count.
        
        Returns:
            Expected question count as string
        """
        return self.question_count_var.get()
    
    def reset(self):
        """Reset the panel state."""
        self.question_count_var.set("0")
        self.progress_var.set(0)
        self.stats_label.config(text="Questions: 0 / 0", foreground=AppTheme.COLORS['text'])
        self._update_button_states(False)
        self.update_undo_redo_state(False, False)
        self.update_training_status(None)
    
    def _on_mark_question(self):
        """Handle mark as question button click."""
        if callable(self.on_mark_question):
            self.on_mark_question()
    
    def _on_mark_answer(self):
        """Handle mark as answer button click."""
        if callable(self.on_mark_answer):
            self.on_mark_answer()
    
    def _on_mark_ignore(self):
        """Handle mark as ignore button click."""
        if callable(self.on_mark_ignore):
            self.on_mark_ignore()
    
    def _on_merge_up(self):
        """Handle merge up button click."""
        if callable(self.on_merge_up):
            self.on_merge_up()
    
    def _on_set_expected_count(self):
        """Handle set expected count button click."""
        if callable(self.on_set_expected_count):
            self.on_set_expected_count()
    
    def _on_undo(self):
        """Handle undo button click."""
        if callable(self.on_undo):
            self.on_undo()
    
    def _on_redo(self):
        """Handle redo button click."""
        if callable(self.on_redo):
            self.on_redo()
    
    def _on_exit(self):
        """Handle exit button click."""
        if callable(self.on_exit):
            self.on_exit()
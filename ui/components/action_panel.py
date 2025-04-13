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
        # Create title frame
        title_frame = ttk.Frame(self, style='TFrame')
        title_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Title label with background
        title_bg = ttk.Frame(title_frame, style='Header.TFrame')
        title_bg.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_bg,
            text="Actions for Selected:",
            style='Header.TLabel',
            font=AppTheme.FONTS['bold']
        )
        title_label.pack(anchor="w", fill=tk.X, padx=5, pady=5)
        
        # Create container for action buttons
        actions_container = ttk.Frame(self, style='TFrame', padding=(3, 5, 3, 5))
        actions_container.pack(fill=tk.X, padx=3, pady=2)
        
        # Action buttons
        self.btn_question = ttk.Button(
            actions_container,
            text="Mark as QUESTION",
            command=self._on_mark_question,
            style='Action.TButton',
            width=20
        )
        self.btn_question.pack(pady=2, fill=tk.X)
        
        self.btn_answer = ttk.Button(
            actions_container,
            text="Mark as ANSWER",
            command=self._on_mark_answer,
            style='Action.TButton',
            width=20
        )
        self.btn_answer.pack(pady=2, fill=tk.X)
        
        self.btn_ignore = ttk.Button(
            actions_container,
            text="Mark as IGNORE",
            command=self._on_mark_ignore,
            style='Action.TButton',
            width=20
        )
        self.btn_ignore.pack(pady=2, fill=tk.X)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Create a separate container for merge action
        merge_container = ttk.Frame(self, style='TFrame', padding=(3, 2, 3, 2))
        merge_container.pack(fill=tk.X, padx=3, pady=2)
        
        # Merge button
        self.btn_merge_up = ttk.Button(
            merge_container,
            text="Add to Previous Answer",
            command=self._on_merge_up,
            style='Action.TButton',
            width=20
        )
        self.btn_merge_up.pack(pady=2, fill=tk.X)
        
        # Add a small tooltip label to explain the functionality
        merge_tooltip = ttk.Label(
            merge_container,
            text="(For multi-paragraph answers)",
            font=("Segoe UI" if AppTheme.FONTS['normal'] is None else AppTheme.FONTS['normal'][0], 7)
        )
        merge_tooltip.pack(pady=(0, 2), fill=tk.X)
        
        # Add undo/redo container
        undo_container = ttk.Frame(self, style='TFrame', padding=(3, 2, 3, 2))
        undo_container.pack(fill=tk.X, padx=3, pady=2)
        
        # Undo/Redo buttons (side by side)
        buttons_frame = ttk.Frame(undo_container)
        buttons_frame.pack(fill=tk.X)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        self.btn_undo = ttk.Button(
            buttons_frame,
            text="↩ Undo",
            command=self._on_undo,
            style='Action.TButton'
        )
        self.btn_undo.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        
        self.btn_redo = ttk.Button(
            buttons_frame,
            text="Redo ↪",
            command=self._on_redo,
            style='Action.TButton'
        )
        self.btn_redo.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Stats container with accent background
        stats_container = ttk.Frame(self, style='TFrame', padding=(10, 10, 10, 10))
        stats_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Expected Question Count Frame
        count_frame = ttk.Frame(stats_container, style='TFrame')
        count_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Expected Questions label with background
        count_bg = ttk.Frame(count_frame, style='Header.TFrame')
        count_bg.pack(side=tk.LEFT)
        
        count_label = ttk.Label(
            count_bg,
            text="Expected # of Questions:",
            style='Header.TLabel',
            font=AppTheme.FONTS['bold']
        )
        count_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        self.question_count_var = tk.StringVar(value="0")
        self.count_entry = ttk.Entry(
            count_frame,
            textvariable=self.question_count_var,
            width=5,
            justify=tk.CENTER
        )
        self.count_entry.pack(side=tk.LEFT, padx=5)
        
        set_count_btn = ttk.Button(
            count_frame,
            text="Set",
            command=self._on_set_expected_count,
            style='Small.Action.TButton',
            width=5
        )
        set_count_btn.pack(side=tk.LEFT)
        
        # Stats title background
        stats_bg = ttk.Frame(stats_container, style='Header.TFrame')
        stats_bg.pack(fill=tk.X, pady=(0, 10))
        
        # Info/Stats Area
        stats_label = ttk.Label(
            stats_bg,
            text="Current Stats:",
            style='Header.TLabel',
            font=AppTheme.FONTS['bold']
        )
        stats_label.pack(anchor="w", fill=tk.X, padx=5, pady=5)
        
        self.stats_label = ttk.Label(
            stats_container,
            text="Questions: 0 / 0",
            font=AppTheme.FONTS['normal']
        )
        self.stats_label.pack(anchor="w", pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            stats_container,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(anchor="w", pady=5, fill=tk.X)
        
        # Training status label (for background training feedback)
        self.training_frame = ttk.Frame(stats_container)
        self.training_frame.pack(fill=tk.X, pady=5)
        
        self.training_status_var = tk.StringVar(value="")
        self.training_status = ttk.Label(
            self.training_frame,
            textvariable=self.training_status_var,
            font=AppTheme.FONTS['normal'],
            foreground=AppTheme.COLORS['accent']
        )
        self.training_status.pack(anchor="w", fill=tk.X)
        
        # Initially hide training status
        self.training_frame.pack_forget()
        
        # Exit button at bottom
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Create a button container for the exit button
        exit_container = ttk.Frame(self, style='TFrame', padding=(3, 2, 3, 2))
        exit_container.pack(fill=tk.X, padx=3, pady=2, side=tk.BOTTOM)
        
        exit_btn = ttk.Button(
            exit_container,
            text="Exit Application",
            command=self._on_exit,
            style='Danger.TButton',
            width=15
        )
        exit_btn.pack(pady=0, side=tk.RIGHT)
        
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
            color = AppTheme.COLORS['dark']
        
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
        self.stats_label.config(text="Questions: 0 / 0")
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
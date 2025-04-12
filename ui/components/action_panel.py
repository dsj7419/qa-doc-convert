"""
Action panel component with direct button fixes.
"""
import tkinter as tk
from tkinter import ttk

from utils.theme import AppTheme, TkButton

class ActionPanel(ttk.Frame):
    """Panel containing action buttons and controls."""
    
    def __init__(self, parent, on_mark_question=None, on_mark_answer=None, 
                 on_mark_ignore=None, on_merge_up=None, on_set_expected_count=None,
                 on_exit=None):
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
        """
        super().__init__(parent, style='TFrame')
        
        self.on_mark_question = on_mark_question
        self.on_mark_answer = on_mark_answer
        self.on_mark_ignore = on_mark_ignore
        self.on_merge_up = on_merge_up
        self.on_set_expected_count = on_set_expected_count
        self.on_exit = on_exit
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Create title background - use tk.Frame for direct color control
        title_bg = tk.Frame(self, bg=AppTheme.COLORS['action_button_bg'], padx=5, pady=5)
        title_bg.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Main title with white text for better contrast
        title_label = tk.Label(
            title_bg,
            text="Actions for Selected:",
            font=AppTheme.FONTS['bold'],
            fg="#ffffff",  # White text
            bg=AppTheme.COLORS['action_button_bg']  # Match the button background
        )
        title_label.pack(anchor="w", fill=tk.X)
        
        # Create container for action buttons with reduced padding
        actions_container = ttk.Frame(self, style='TFrame', padding=(3, 5, 3, 5))
        actions_container.pack(fill=tk.X, padx=3, pady=2)
        
        # DIRECT APPROACH: Use plain tk.Button for the 4 main action buttons
        # Button 1: Mark as QUESTION - pure Tkinter button with explicit white text
        self.btn_question = tk.Button(
            actions_container,
            text="Mark as QUESTION",
            command=self._on_mark_question,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # DIRECT WHITE TEXT 
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=20,
            height=1
        )
        self.btn_question.pack(pady=2, fill=tk.X)
        
        # Button 2: Mark as ANSWER - pure Tkinter button with explicit white text
        self.btn_answer = tk.Button(
            actions_container,
            text="Mark as ANSWER",
            command=self._on_mark_answer,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # DIRECT WHITE TEXT
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=20,
            height=1
        )
        self.btn_answer.pack(pady=2, fill=tk.X)
        
        # Button 3: Mark as IGNORE - pure Tkinter button with explicit white text
        self.btn_ignore = tk.Button(
            actions_container,
            text="Mark as IGNORE",
            command=self._on_mark_ignore,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # DIRECT WHITE TEXT
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=20,
            height=1
        )
        self.btn_ignore.pack(pady=2, fill=tk.X)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Create a separate container for merge action - more compact
        merge_container = ttk.Frame(self, style='TFrame', padding=(3, 2, 3, 2))
        merge_container.pack(fill=tk.X, padx=3, pady=2)
        
        # Button 4: Add to Previous Answer - pure Tkinter button with explicit white text
        self.btn_merge_up = tk.Button(
            merge_container,
            text="Add to Previous Answer",
            command=self._on_merge_up,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # DIRECT WHITE TEXT
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=20,
            height=1
        )
        self.btn_merge_up.pack(pady=2, fill=tk.X)
        
        # Add a small tooltip label to explain the functionality
        merge_tooltip = tk.Label(
            merge_container,
            text="(For multi-paragraph answers)",
            font=(AppTheme.FONTS['normal'][0], 7),
            fg="#555555",
            bg=AppTheme.COLORS['bg']
        )
        merge_tooltip.pack(pady=(0, 2), fill=tk.X)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Stats container with accent background
        stats_container = ttk.Frame(self, style='TFrame', padding=(10, 10, 10, 10))
        stats_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Expected Question Count Frame with better visual design
        count_frame = ttk.Frame(stats_container, style='TFrame')
        count_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Expected Questions label with better contrast - use tk.Frame for direct color control
        count_label_container = tk.Frame(count_frame, bg=AppTheme.COLORS['action_button_bg'])
        count_label_container.pack(side=tk.LEFT)
        
        count_label = tk.Label(
            count_label_container,
            text="Expected # of Questions:",
            font=AppTheme.FONTS['bold'],
            fg="#ffffff",  # White text
            bg=AppTheme.COLORS['action_button_bg']
        )
        count_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        self.question_count_var = tk.StringVar(value="0")
        self.count_entry = ttk.Entry(
            count_frame,
            textvariable=self.question_count_var,
            width=5,
            justify=tk.CENTER,
            style='TEntry'
        )
        self.count_entry.pack(side=tk.LEFT, padx=5)
        
        # Replace ttk.Button with a standard tk.Button for consistent styling
        set_count_btn = tk.Button(
            count_frame,
            text="Set",
            command=self._on_set_expected_count,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # DIRECT WHITE TEXT
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=5
        )
        set_count_btn.pack(side=tk.LEFT)
        
        # Stats title with styling - use tk.Frame for direct color control
        stats_title_bg = tk.Frame(stats_container, bg=AppTheme.COLORS['action_button_bg'])
        stats_title_bg.pack(fill=tk.X, pady=(0, 10))
        
        # Info/Stats Area with enhanced styling
        stats_label = tk.Label(
            stats_title_bg,
            text="Current Stats:",
            font=AppTheme.FONTS['bold'],
            fg="#ffffff",  # White text
            bg=AppTheme.COLORS['action_button_bg']
        )
        stats_label.pack(anchor="w", fill=tk.X, padx=5, pady=5)
        
        self.stats_label = ttk.Label(
            stats_container,
            text="Questions: 0 / 0",
            font=AppTheme.FONTS['normal']
        )
        self.stats_label.pack(anchor="w", pady=(0, 5))
        
        # Progress bar with better styling
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            stats_container,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate',
            variable=self.progress_var,
            style='TProgressbar'
        )
        self.progress_bar.pack(anchor="w", pady=5, fill=tk.X)
        
        # Exit button at bottom
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Create a button container for the exit button - more compact
        exit_container = ttk.Frame(self, style='TFrame', padding=(3, 2, 3, 2))
        exit_container.pack(fill=tk.X, padx=3, pady=2, side=tk.BOTTOM)
        
        exit_btn = TkButton(
            exit_container,
            text="Exit Application",
            command=self._on_exit,
            style='danger',
            width=15,  # Reduced width
            height=1,  # Reduced height
            padx=3,    # Reduced padding
            pady=1     # Reduced padding
        )
        exit_btn.pack(pady=0, side=tk.RIGHT)
        
        # Initially disable action buttons
        self._update_button_states(False)
    
    def _update_button_states(self, enabled):
        """
        Update button states based on selection.
        
        Args:
            enabled: Whether buttons should be enabled
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        
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
    
    def _on_multi_question(self):
        """Handle mark all as question button click."""
        if callable(self.on_multi_question):
            self.on_multi_question()
    
    def _on_multi_answer(self):
        """Handle mark all as answer button click."""
        if callable(self.on_multi_answer):
            self.on_multi_answer()
    
    def _on_multi_ignore(self):
        """Handle mark all as ignore button click."""
        if callable(self.on_multi_ignore):
            self.on_multi_ignore()
    
    def _on_set_expected_count(self):
        """Handle set expected count button click."""
        if callable(self.on_set_expected_count):
            self.on_set_expected_count()
    
    def _on_exit(self):
        """Handle exit button click."""
        if callable(self.on_exit):
            self.on_exit()
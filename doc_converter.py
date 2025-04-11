import tkinter as tk
from tkinter import ttk  # For themed widgets like Separator
from tkinter import filedialog, messagebox, scrolledtext
import docx
import re
import csv
import os
import platform
import subprocess
import logging
from enum import Enum, auto

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Enums for Paragraph Roles ---
class ParaRole(Enum):
    QUESTION = auto()
    ANSWER = auto()
    IGNORE = auto() # For headers, footers, formatting, etc.
    UNDETERMINED = auto() # Initial state

# --- UI Configuration ---
COLORS = {
    'bg': "#f0f0f0",
    'header_bg': "#4a7abc",
    'header_fg': "white",
    'button_bg': "#4CAF50",
    'button_fg': "white",
    'action_button_bg': "#ff9800", # Orange for actions
    'action_button_fg': "white",
    'exit_bg': "#f44336",
    'exit_fg': "white",
    'list_bg': 'white',
    'list_sel_bg': '#c3e1ff', # Light blue selection
    'role_question_bg': '#d0f0c0', # Light green
    'role_answer_bg': '#ffffff',   # White
    'role_ignore_bg': '#e0e0e0',   # Grey
    'role_undetermined_bg': '#fffacd', # Lemon chiffon
}

FONTS = {
    'normal': ("Segoe UI", 10),
    'bold': ("Segoe UI", 10, "bold"),
    'title': ("Segoe UI", 16, "bold"),
    'log': ("Consolas", 9),
    'list': ("Segoe UI", 10),
}

# --- Heuristic Extraction Function (Your Version 9.0 - slightly adapted) ---
# Note: This now returns the *indices* of the top 50 potential questions,
# rather than the fully processed Q&A structure.
def get_initial_question_indices(paragraphs, update_status):
    """
    Uses heuristic scoring to identify the initial top 50 potential question paragraphs.
    Returns a sorted list of paragraph indices.
    """
    update_status("Running initial heuristic analysis...")
    expected_count = 50 # Hardcoded for this purpose

    potential_questions = []
    # Map original index to paragraph text for scoring
    para_map = {i: p for i, p in enumerate(paragraphs)}

    # This loop and scoring logic is directly from your Version 9.0
    for i, p in enumerate(paragraphs):
        if len(p) < 10: continue
        if p.startswith(('```', '<!--', '-->')): continue
        # Removed the explicit skip for '1. Answer' and '>' here,
        # Relying on scoring penalties instead for more flexibility.

        has_question_mark = '?' in p
        has_question_words = any(word in p.lower() for word in
                         ['what', 'when', 'where', 'why', 'how', 'name', 'list',
                          'identify', 'describe', 'define', 'explain'])
        has_numeric_reference = bool(re.search(r'(\d+)\s+(kinds|types|requirements|grounds|factors|situations|matters|things)', p, re.IGNORECASE))
        is_question_like = (
            p.lower().startswith(('what', 'when', 'where', 'why', 'how', 'name', 'is ', 'are ', 'does ')) or
            re.search(r'(what is|what are|name the|which|how many)', p.lower())
        )

        if has_question_mark or has_question_words or has_numeric_reference or is_question_like:
            potential_questions.append((i, p)) # Store index and text

    update_status(f"Found {len(potential_questions)} potential questions based on initial keywords/structure.")

    scored_questions = []
    for idx, text in potential_questions:
        score = 0
        if '?' in text: score += 10
        if re.match(r'^(What|When|Where|Why|How|Name|Which|Is|Are|Does|Do)\b', text, re.IGNORECASE): score += 8
        if any(word in text.lower() for word in ['what', 'when', 'where', 'why', 'how']): score += 5
        if any(word in text.lower() for word in ['name', 'list', 'identify', 'describe', 'define']): score += 5
        if re.search(r'(\d+)\s+(kinds|types|requirements|grounds|factors|situations|matters|things)', text, re.IGNORECASE): score += 7
        if len(text) > 30: score += 3
        # Simplified next paragraph check - less reliable, weighted lower
        if idx < len(paragraphs) - 1 and re.match(r'^\s*\d+[\.\)]', para_map.get(idx + 1, '')): score += 2
        if text.startswith(('The ', 'A ', 'An ', 'Both ', 'It ', 'PC', 'BRO', 'LAC', '1.', '2.', '3.', 'a.', 'b.')): score -= 5 # Penalize typical answer starts
        if text.isupper() or text.startswith('**'): score -= 3

        # Big boost if it *actually* starts with a number/dot/space pattern,
        # even if python-docx strips it, the pattern *might* appear if typed manually
        if re.match(r"^\s*\d+\s*[\.\)]\s+", text):
            score += 15

        # Only add if score is reasonably positive
        if score > 0:
           scored_questions.append({'index': idx, 'text': text, 'score': score})

    scored_questions.sort(key=lambda x: x['score'], reverse=True)
    update_status(f"Scored {len(scored_questions)} potential questions.")

    # Take top 50 based purely on score
    top_scored_indices = {q['index'] for q in scored_questions[:expected_count]}

    update_status(f"Identified initial {len(top_scored_indices)} candidates for questions.")
    return top_scored_indices

# --- Main Application Class ---
class QAVerifierApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Q&A Verifier")
        self.geometry("950x750")
        self.configure(bg=COLORS['bg'])

        self.file_path = None
        self.all_paragraphs = [] # List of {'index': int, 'text': str, 'role': ParaRole, 'q_num': int|None}
        self.current_selection_index = -1 # Index within the listbox/all_paragraphs

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['header_bg'], padx=15, pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="Interactive Q&A Verifier", font=FONTS['title'], bg=COLORS['header_bg'], fg=COLORS['header_fg']).pack()

        # --- Top Controls ---
        top_controls = tk.Frame(self, bg=COLORS['bg'], padx=10, pady=10)
        top_controls.pack(fill=tk.X)

        load_btn = tk.Button(top_controls, text="Load DOCX File", command=self.load_file, font=FONTS['bold'], bg=COLORS['button_bg'], fg=COLORS['button_fg'], width=15)
        load_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.status_var = tk.StringVar(value="Load a DOCX file to begin.")
        status_label = tk.Label(top_controls, textvariable=self.status_var, font=FONTS['normal'], bg=COLORS['bg'], anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        save_btn = tk.Button(top_controls, text="Save Corrected CSV", command=self.save_csv, font=FONTS['bold'], bg=COLORS['button_bg'], fg=COLORS['button_fg'], width=20)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))


        # --- Main Content Area (Paragraph List and Actions) ---
        main_frame = tk.Frame(self, bg=COLORS['bg'], padx=10, pady=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=3) # Paragraph list takes more space
        main_frame.columnconfigure(1, weight=0) # Separator
        main_frame.columnconfigure(2, weight=1) # Actions
        main_frame.rowconfigure(0, weight=1)

        # Paragraph Listbox Frame
        list_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        list_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)

        tk.Label(list_frame, text="Document Paragraphs:", font=FONTS['bold'], bg=COLORS['bg']).grid(row=0, column=0, sticky="w")

        self.para_listbox = tk.Listbox(list_frame, font=FONTS['list'], bg=COLORS['list_bg'],
                                      selectbackground=COLORS['list_sel_bg'], selectforeground='black',
                                      borderwidth=1, relief=tk.SUNKEN, exportselection=False)
        self.para_listbox.grid(row=1, column=0, sticky="nsew")

        list_scroll_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.para_listbox.yview)
        list_scroll_y.grid(row=1, column=1, sticky="ns")
        self.para_listbox.config(yscrollcommand=list_scroll_y.set)

        list_scroll_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.para_listbox.xview)
        list_scroll_x.grid(row=2, column=0, sticky="ew")
        self.para_listbox.config(xscrollcommand=list_scroll_x.set)

        self.para_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        # Separator
        sep = ttk.Separator(main_frame, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="ns", padx=5)

        # Action Panel Frame
        action_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        action_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        tk.Label(action_frame, text="Actions for Selected:", font=FONTS['bold'], bg=COLORS['bg']).pack(anchor="w", pady=(0, 10))

        # Action Buttons (using pack within the action_frame)
        btn_config = {'font': FONTS['normal'], 'bg': COLORS['action_button_bg'], 'fg': COLORS['action_button_fg'], 'width': 20, 'pady': 3}

        btn_question = tk.Button(action_frame, text="Mark as QUESTION", command=lambda: self.change_role(ParaRole.QUESTION), **btn_config)
        btn_question.pack(pady=3, fill=tk.X)

        btn_answer = tk.Button(action_frame, text="Mark as ANSWER", command=lambda: self.change_role(ParaRole.ANSWER), **btn_config)
        btn_answer.pack(pady=3, fill=tk.X)

        btn_ignore = tk.Button(action_frame, text="Mark as IGNORE", command=lambda: self.change_role(ParaRole.IGNORE), **btn_config)
        btn_ignore.pack(pady=3, fill=tk.X)

        tk.Label(action_frame, text="", bg=COLORS['bg']).pack(pady=5) # Spacer

        btn_merge_up = tk.Button(action_frame, text="Merge into Prev. Answer", command=self.merge_up, **btn_config)
        btn_merge_up.pack(pady=3, fill=tk.X)

        tk.Label(action_frame, text="", bg=COLORS['bg']).pack(pady=5) # Spacer

        # Info/Stats Area
        tk.Label(action_frame, text="Current Stats:", font=FONTS['bold'], bg=COLORS['bg']).pack(anchor="w", pady=(15, 5))
        self.stats_label = tk.Label(action_frame, text="Questions: 0 / 50", font=FONTS['normal'], bg=COLORS['bg'], justify=tk.LEFT)
        self.stats_label.pack(anchor="w")

        tk.Label(action_frame, text="", bg=COLORS['bg']).pack(pady=15) # Spacer

        exit_btn = tk.Button(action_frame, text="Exit Application", command=self.quit, font=FONTS['normal'], bg=COLORS['exit_bg'], fg=COLORS['exit_fg'], width=20)
        exit_btn.pack(pady=20, side=tk.BOTTOM)

        # --- Log Area ---
        log_frame = tk.Frame(self, bg=COLORS['bg'], padx=10)
        log_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(log_frame, text="Log:", font=FONTS['bold'], bg=COLORS['bg']).pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=FONTS['log'], bg="white",
                                                relief=tk.SUNKEN, bd=1, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.X)

    # --- Backend Logic ---

    def log_message(self, message, level="INFO"):
        """Adds a message to the log area and logger."""
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{level}: {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks() # Keep UI responsive

    def update_status(self, message):
        """Updates the status bar."""
        self.status_var.set(message)
        self.update_idletasks()

    def load_file(self):
        """Loads a DOCX file, extracts paragraphs, runs initial analysis."""
        path = filedialog.askopenfilename(
            title="Select DOCX File",
            filetypes=[("Word Documents", "*.docx")]
        )
        if not path:
            self.update_status("File selection cancelled.")
            return

        self.file_path = path
        self.update_status(f"Loading: {os.path.basename(path)}...")
        self.log_message(f"Selected file: {path}")

        try:
            doc = docx.Document(self.file_path)
            raw_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and not p.text.isspace()]
            self.log_message(f"Extracted {len(raw_paragraphs)} non-empty paragraphs.")

            if not raw_paragraphs:
                messagebox.showerror("Error", "Document contains no readable text.")
                return

            # Run initial heuristic
            initial_q_indices = get_initial_question_indices(raw_paragraphs, self.log_message)

            # Create the main data structure
            self.all_paragraphs = []
            current_q_num = 0
            last_role = ParaRole.UNDETERMINED

            for i, text in enumerate(raw_paragraphs):
                role = ParaRole.UNDETERMINED
                q_num = None
                if i in initial_q_indices:
                    role = ParaRole.QUESTION
                    current_q_num += 1
                    q_num = current_q_num
                elif last_role == ParaRole.QUESTION or last_role == ParaRole.ANSWER:
                    # If the previous was Q or A, assume this is an Answer
                    role = ParaRole.ANSWER
                    q_num = current_q_num # Assign to the last seen question
                else:
                    # Could be header or undetermined
                    # Let's mark short starting lines as IGNORE potentially
                    if i < 5 and len(text) < 50: # Crude header check
                         role = ParaRole.IGNORE
                    else:
                         role = ParaRole.UNDETERMINED # Default

                self.all_paragraphs.append({'index': i, 'text': text, 'role': role, 'q_num': q_num})
                # Update last_role *after* appending, using the role just assigned
                last_role = role


            self.log_message(f"Initial analysis complete. Identified {current_q_num} potential questions.")
            self.refresh_listbox()
            self.update_stats()
            self.update_status("Ready for verification. Select a paragraph.")

        except Exception as e:
            self.log_message(f"Error loading or processing file: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to load or process the document:\n{e}")
            self.file_path = None
            self.all_paragraphs = []
            self.para_listbox.delete(0, tk.END)


    def refresh_listbox(self):
        """Updates the listbox display based on self.all_paragraphs."""
        self.para_listbox.delete(0, tk.END)
        q_counter = 0
        for i, para_data in enumerate(self.all_paragraphs):
            role = para_data['role']
            text = para_data['text']
            prefix = ""
            bg_color = COLORS['role_undetermined_bg']

            if role == ParaRole.QUESTION:
                q_counter += 1
                prefix = f"Q{q_counter}: "
                bg_color = COLORS['role_question_bg']
            elif role == ParaRole.ANSWER:
                prefix = f"  A{para_data['q_num']}: "
                bg_color = COLORS['role_answer_bg']
            elif role == ParaRole.IGNORE:
                prefix = "[IGNORE]: "
                bg_color = COLORS['role_ignore_bg']
            else: # UNDETERMINED
                prefix = "[?]: "

            display_text = f"{prefix}{text}"
            self.para_listbox.insert(tk.END, display_text)
            self.para_listbox.itemconfig(i, {'bg': bg_color})

        # Try to reselect the previously selected item if possible
        if 0 <= self.current_selection_index < len(self.all_paragraphs):
             self.para_listbox.selection_set(self.current_selection_index)
             self.para_listbox.activate(self.current_selection_index)
             self.para_listbox.see(self.current_selection_index)
        else:
             self.current_selection_index = -1


    def update_stats(self):
        """Calculates and displays the current number of questions."""
        question_count = sum(1 for p in self.all_paragraphs if p['role'] == ParaRole.QUESTION)
        status = f"Questions: {question_count} / 50"
        color = "green" if question_count == 50 else "red"
        self.stats_label.config(text=status, fg=color)
        return question_count

    def on_listbox_select(self, event):
        """Handles selection changes in the listbox."""
        selected_indices = self.para_listbox.curselection()
        if selected_indices:
            self.current_selection_index = selected_indices[0]
            # You could add code here to display more details about the selected paragraph if needed
            # For now, selection mainly enables the action buttons
        else:
            self.current_selection_index = -1


    def renumber_and_refresh(self):
        """Iterates through paragraphs, assigns sequential q_num, and refreshes UI."""
        self.log_message("Renumbering questions and refreshing display...")
        q_counter = 0
        current_q_num_for_answers = 0
        for para_data in self.all_paragraphs:
            if para_data['role'] == ParaRole.QUESTION:
                q_counter += 1
                para_data['q_num'] = q_counter
                current_q_num_for_answers = q_counter
            elif para_data['role'] == ParaRole.ANSWER:
                # Assign answer to the most recently seen question number
                para_data['q_num'] = current_q_num_for_answers
            else: # IGNORE or UNDETERMINED
                para_data['q_num'] = None
        self.refresh_listbox()
        self.update_stats()
        self.log_message("Renumbering complete.")


    def change_role(self, new_role):
        """Changes the role of the selected paragraph(s)."""
        selected_indices = self.para_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select one or more paragraphs to change their role.")
            return

        indices_to_change = list(selected_indices) # Get actual list indices

        self.log_message(f"Changing role to {new_role.name} for {len(indices_to_change)} paragraph(s).")

        needs_renumber = False
        for idx in indices_to_change:
            if 0 <= idx < len(self.all_paragraphs):
                old_role = self.all_paragraphs[idx]['role']
                self.all_paragraphs[idx]['role'] = new_role
                # If changing to/from QUESTION, we need to renumber
                if old_role == ParaRole.QUESTION or new_role == ParaRole.QUESTION:
                    needs_renumber = True

        if needs_renumber:
            self.renumber_and_refresh()
        else:
            # Just refresh colors/prefixes without full renumber
            self.refresh_listbox()
            self.update_stats() # Stats might change if IGNORE -> ANSWER etc.


    def merge_up(self):
        """Marks the selected paragraph(s) as ANSWER belonging to the previous question."""
        selected_indices = self.para_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select paragraph(s) to merge into the preceding answer block.")
            return

        indices_to_merge = sorted(list(selected_indices)) # Process in order

        self.log_message(f"Attempting to merge {len(indices_to_merge)} paragraph(s) into previous answer.")

        needs_renumber = False
        for idx in indices_to_merge:
            if idx == 0:
                self.log_message(f"Cannot merge up paragraph at index 0.", "WARNING")
                continue # Cannot merge the very first paragraph

            if 0 < idx < len(self.all_paragraphs):
                 # Find the effective q_num of the *preceding* block
                preceding_q_num = None
                for prev_idx in range(idx - 1, -1, -1):
                    if self.all_paragraphs[prev_idx]['q_num'] is not None:
                        preceding_q_num = self.all_paragraphs[prev_idx]['q_num']
                        break

                if preceding_q_num is not None:
                    old_role = self.all_paragraphs[idx]['role']
                    self.all_paragraphs[idx]['role'] = ParaRole.ANSWER
                    self.all_paragraphs[idx]['q_num'] = preceding_q_num
                    # If it was a QUESTION, we need renumbering
                    if old_role == ParaRole.QUESTION:
                        needs_renumber = True
                else:
                     self.log_message(f"Could not find a preceding question/answer block for paragraph at index {idx}.", "WARNING")


        if needs_renumber:
            self.renumber_and_refresh()
        else:
            self.refresh_listbox()
            self.update_stats()

    def save_csv(self):
        """Validates and saves the corrected Q&A pairs to a CSV file."""
        if not self.file_path:
            messagebox.showerror("Error", "No file loaded.")
            return
        if not self.all_paragraphs:
            messagebox.showerror("Error", "No paragraph data available.")
            return

        self.log_message("Preparing to save CSV...")

        # --- Data Aggregation ---
        questions_data = {} # {q_num: {'question': text, 'answers': [text]}}
        final_questions = [] # Ordered list of dicts
        q_count = 0

        # First pass: Collect questions
        for para in self.all_paragraphs:
            if para['role'] == ParaRole.QUESTION:
                q_num = para['q_num']
                if q_num is not None:
                     q_count += 1
                     questions_data[q_num] = {'number': q_num, 'question': para['text'], 'answers': []}

        # --- Validation ---
        if q_count != 50:
            response = messagebox.askokcancel("Incorrect Question Count",
                                       f"You currently have {q_count} paragraphs marked as questions.\n"
                                       f"Exactly 50 are required to save.\n\n"
                                       f"Press OK to cancel saving and continue editing, or Cancel to abort.")
            if response or not response: # If OK or Cancel clicked (or window closed)
                 self.log_message(f"Save cancelled. Question count ({q_count}) is not 50.", "WARNING")
                 return


        # Second pass: Collect answers and order
        for q_num in sorted(questions_data.keys()):
            # Find answers associated with this q_num
            answers = [p['text'] for p in self.all_paragraphs if p['role'] == ParaRole.ANSWER and p['q_num'] == q_num]
            questions_data[q_num]['answers'] = answers
            final_questions.append(questions_data[q_num])


        # --- Get Save Path ---
        output_csv_path = os.path.splitext(self.file_path)[0] + "_verified.csv"
        save_path = filedialog.asksaveasfilename(
            title="Save Verified CSV",
            initialfile=os.path.basename(output_csv_path),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not save_path:
            self.log_message("CSV save cancelled by user.")
            return

        # --- Write to CSV ---
        try:
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for q in final_questions:
                    # Format: Question Number. Question Text in first column
                    # Answer paragraphs in subsequent columns
                    row = [f"{q['number']}. {q['question']}"] + q['answers']
                    writer.writerow(row)

            self.log_message(f"Successfully saved verified data to: {save_path}")
            messagebox.showinfo("Save Successful", f"Verified Q&A data saved to:\n{save_path}")

            # Ask to open file
            if messagebox.askyesno("Open File?", f"CSV saved successfully.\n\nWould you like to open the file?"):
                 self._open_file_externally(save_path)

        except Exception as e:
            self.log_message(f"Failed to write CSV file: {e}", "ERROR")
            messagebox.showerror("Save Error", f"Could not save the CSV file:\n{e}")


    def _open_file_externally(self, file_to_open):
        """Attempts to open the specified file using the OS default application."""
        try:
            if platform.system() == 'Windows':
                os.startfile(file_to_open)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_to_open])
            else:  # Linux and others
                subprocess.call(['xdg-open', file_to_open])
            self.log_message(f"Attempting to open {file_to_open} externally.")
        except Exception as open_err:
             self.log_message(f"Could not automatically open file: {open_err}", "WARNING")
             messagebox.showwarning("Open File Error",
                                  f"Could not automatically open the file.\nPlease navigate to it manually:\n{file_to_open}")

# --- Entry Point ---
if __name__ == "__main__":
    app = QAVerifierApp()
    app.mainloop()
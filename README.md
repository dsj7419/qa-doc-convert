# QA Verifier Professional Edition

A professional tool for verifying and processing Q&A documents, designed to convert Word documents into CSV format for use in various educational and testing applications.

## Features

- **AI-Powered Analysis**: Automatically recognizes questions and answers using a transformer-based AI model with ONNX acceleration
- **Smart Question Detection**: Automatically recognizes questions based on content analysis and formatting patterns
- **Flexible Question Count**: Works with any number of questions, not limited to a fixed count
- **Interactive Editing**: Easily mark paragraphs as questions, answers, or items to ignore
- **Bulk Operations**: Efficiently process multiple paragraphs at once
- **Filtering**: Quickly find specific content in large documents
- **Progress Tracking**: Visual indication of completion status
- **Multi-level Undo/Redo**: Complete support for reverting and reapplying changes
- **Professional UI**: Clean, modern interface with a professional color scheme
- **CSV Export**: Generate properly formatted CSV files ready for import into other systems
- **Background Training**: AI model trains in the background while you work
- **Intelligent Recovery**: Automatically resumes training after interruptions

## Installation

### Option 1: Using the Installer

1. Download the latest installer from the [releases page](https://github.com/yourusername/qa-verifier-pro/releases)
2. Run the installer and follow the on-screen instructions
3. Launch QA Verifier from your applications menu or desktop shortcut

### Option 2: From Source

1. Clone this repository:

    ```bash
    git clone https://github.com/yourusername/qa-verifier-pro.git
    cd qa-verifier-pro
    ```

2. Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:

    ```bash
    python main.py
    ```

### Option 3: Build Executable

1. Install PyInstaller:

    ```bash
    pip install pyinstaller
    ```

2. Build the executable:

    ```bash
    pyinstaller QAVerifier.spec
    ```

3. Find the executable in the `dist/QA Verifier Pro` directory

## Usage

### Basic Workflow

1. Click "Load DOCX File" to open a Word document
2. Review the automatically identified questions and answers
3. Use the action buttons to correct any misidentified paragraphs:
   - "Mark as QUESTION" - Mark selected paragraph as a question
   - "Mark as ANSWER" - Mark selected paragraph as an answer
   - "Mark as IGNORE" - Mark selected paragraph as content to ignore
   - "Add to Previous Answer" - Combine with the preceding answer paragraph
4. When satisfied, click "Save Corrected CSV" to export the verified Q&A pairs

### Keyboard Shortcuts

- **Ctrl+O**: Open DOCX file
- **Ctrl+S**: Save CSV file
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+Q**: Mark as Question
- **Ctrl+A**: Mark as Answer
- **Ctrl+I**: Mark as Ignore
- **Ctrl+M**: Add to Previous Answer

### Multiple Selection

You can select multiple paragraphs at once using:
- **Ctrl+Click** (or **Cmd+Click** on Mac) to select individual paragraphs
- **Shift+Click** to select a range of paragraphs

Then use the Action buttons to quickly mark several paragraphs at once.

### Filtering

The filter box allows you to quickly find specific content in large documents:
1. Type search text in the filter box
2. Only paragraphs containing the search text will be shown
3. Click "Clear" to show all paragraphs again

### AI Features

The application includes an AI model that improves over time:
- The AI learns from your corrections and gets better at identifying questions and answers
- Training happens automatically in the background when you save files
- You can monitor training progress in the application logs
- Training will automatically resume if interrupted

## Architecture

QA Verifier Professional Edition is built using the Model-View-Presenter (MVP) pattern:

- **Model**: Document and Paragraph classes represent the data
- **View**: MainWindow and UI components handle the user interface
- **Presenter**: MainPresenter coordinates between model and view

Additional architectural patterns:
- **Command Pattern**: Used for undo/redo functionality
- **Strategy Pattern**: Different analyzers for question identification
- **Factory Pattern**: Used to create the appropriate analyzer

## Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- Windows 10/11, macOS 11+, or Linux with GUI support

## Development

### Running Tests

Run tests with coverage:

```bash
pytest --cov=. --cov-report=html
```

Coverage reports will be generated in the `coverage_html_report` directory.

### Building Distributions

Build standalone executable:

```bash
pip install pyinstaller
pyinstaller QAVerifier.spec
```

Built executables will be available in the `dist` directory.

### Create Windows Installer

Build an installer using Inno Setup:

```bash
iscc qa_verifier_installer.iss
```

The installer will be created in the `installer` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
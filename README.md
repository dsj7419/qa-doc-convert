# QA Verifier Professional Edition

A professional tool for verifying and processing Q&A documents, designed to convert Word documents into CSV format for use in various educational and testing applications.

## Features

- **Smart Question Detection**: Automatically recognizes questions in documents based on content analysis
- **Flexible Question Count**: Works with any number of questions, not limited to a fixed count
- **Interactive Editing**: Easily mark paragraphs as questions, answers, or items to ignore
- **Bulk Operations**: Efficiently process multiple paragraphs at once
- **Filtering**: Quickly find specific content in large documents
- **Progress Tracking**: Visual indication of completion status
- **Professional UI**: Clean, modern interface with a professional color scheme
- **CSV Export**: Generate properly formatted CSV files ready for import into other systems

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/qa-verifier-pro.git
   cd qa-verifier-pro
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Click "Load DOCX File" to open a Word document
3. Review the automatically identified questions and answers
4. Use the action buttons to correct any misidentified paragraphs:
   - "Mark as QUESTION" - Mark selected paragraph as a question
   - "Mark as ANSWER" - Mark selected paragraph as an answer
   - "Mark as IGNORE" - Mark selected paragraph as content to ignore
   - "Merge into Prev. Answer" - Combine with the preceding answer paragraph
5. When satisfied, click "Save Corrected CSV" to export the verified Q&A pairs

## Multiple Selection

You can select multiple paragraphs at once using:
- **Ctrl+Click** (or **Cmd+Click** on Mac) to select individual paragraphs
- **Shift+Click** to select a range of paragraphs

Then use the Multiple Selection Actions buttons to quickly mark several paragraphs at once.

## Filtering

The filter box allows you to quickly find specific content in large documents:
1. Type search text in the filter box
2. Only paragraphs containing the search text will be shown
3. Click "Clear" to show all paragraphs again

## License

This project is licensed under the MIT License - see the LICENSE file for details.
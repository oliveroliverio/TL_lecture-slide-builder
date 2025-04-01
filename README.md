# Screen Capture Utility

A Python utility for capturing screens from specific monitors and saving the images.

## Prerequisites

- Python 3.8+
- [UV pip](https://github.com/astral-sh/uv) (recommended) or pip
- FFmpeg (if working with video files)
- Tesseract OCR (for text extraction)
- Deepseek API key (for title generation)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/example/repo.git
   cd repo
   ```

2. **Set up a virtual environment**:
   ```bash
   uv venv
   ```

3. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```cmd
     .venv\Scripts\activate
     ```

4. **Install dependencies**:
   - *given a pyproject.toml file, install dependencies using uv pip*
   ```bash
   uv pip install .
   ```
   - *otherwise, if project has `requirements.txt`, install dependencies like this*
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Install Tesseract OCR**:
   - On macOS:
     ```bash
     brew install tesseract
     ```
   - On Ubuntu/Debian:
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   - On Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

6. **Configure API key**:
   - Create a `.env` file in the root directory with your Deepseek API key:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     ```

## Usage

1. **Identify your monitor**:
   Run the following command to view available monitors and their indexes:
   ```bash
   python view-screen-indexes.py
   ```
   Note the index of the monitor you want to capture.

2. **Prepare your video**:
   - Open the video you want to capture from on the desired monitor
   - Ensure it's playing in full screen for best results

3. **Run the capture utility**:
   ```bash
   python generate_slides.py
   ```
   The script will capture screenshots from the specified monitor.

## Features

### Slide Capture
- Automatically captures slides from presentations
- Detects and skips frames with presenter faces
- Compares images to avoid duplicates
- Saves timestamped PNG images

### OCR and Title Generation (New)
- Extracts text from captured slides using OCR
- Generates descriptive titles based on slide content using Deepseek AI
- Renames files with original timestamp plus the generated title
- Runs in parallel to avoid interrupting the slide capture process

## Configuration

You can modify the following aspects of the capture utility by editing `generate_slides.py`:
- Output directory for captured images
- Capture interval
- Image format (PNG, JPEG, etc.)
- Monitor selection (if multiple monitors are available)
- Maximum title length
- OCR queue size

## Troubleshooting

- If you get monitor-related errors, double check your monitor index using `view-screen-indexes.py`
- Ensure no other applications are obscuring the video playback window
- For performance issues, try reducing the capture resolution
- If OCR is not working, ensure Tesseract is properly installed and accessible in your PATH
- If title generation fails, check your Deepseek API key and internet connection

## License

[MIT](LICENSE)




Roadmap:
- Automatic title generation based on OCR of images 
- Project description
- Specific configuration options
- Example images/screenshots
- Contribution guidelines
- Known issues
- Roadmap/planned features

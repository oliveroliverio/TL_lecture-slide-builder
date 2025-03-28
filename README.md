
# Screen Capture Utility

A Python utility for capturing screens from specific monitors and saving the images.

## Prerequisites

- Python 3.8+
- [UV pip](https://github.com/astral-sh/uv) (recommended) or pip
- FFmpeg (if working with video files)

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
   ```bash
   uv pip install .
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
   python main.py
   ```
   The script will capture screenshots from the specified monitor.

## Configuration

You can modify the following aspects of the capture utility by editing `main.py`:
- Output directory for captured images
- Capture interval
- Image format (PNG, JPEG, etc.)
- Monitor selection (if multiple monitors are available)

## Troubleshooting

- If you get monitor-related errors, double check your monitor index using `view-screen-indexes.py`
- Ensure no other applications are obscuring the video playback window
- For performance issues, try reducing the capture resolution

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

# JSON Configuration Visualizer

This repository contains a simple Tkinter application for exploring Open Components System (OCS) JSON configuration files.

Features include:

- Load one or more JSON files for inspection
- View each configuration section in its own tab with optional tooltips
- Tooltip text is stored in `tooltip.py` for easy customization
- Search across all fields for quick navigation
- Diff view between the first two files when `jsondiff` is installed
- Heatmap comparison across all loaded files
- Light and dark mode with automatic theme detection
- Tabs load lazily for improved performance

## Requirements

- Python 3
- Tkinter (usually bundled with Python)
- [`jsondiff`](https://pypi.org/project/jsondiff/) (optional; provides diff view)
- [`darkdetect`](https://pypi.org/project/darkdetect/) (optional; detects OS theme)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the visualizer with:

```bash
python json_visualizer.py
```

Use the **Upload JSON File(s)** button to load any number of configuration files. When multiple files are provided, a heatmap window summarizes their differences and a detailed diff between the first two files is also available.

## License

This project is released under the MIT License.

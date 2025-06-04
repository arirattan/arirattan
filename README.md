# JSON Configuration Visualizer

This repository contains a simple Tkinter application for exploring Open Components System (OCS) JSON configuration files.

Features include:

- Load one or two JSON files for inspection
- View each configuration section in its own tab with optional tooltips
- Search across all fields for quick navigation
- Diff view between two files when `jsondiff` is installed

## Requirements

- Python 3
- Tkinter (usually bundled with Python)
- [`jsondiff`](https://pypi.org/project/jsondiff/) (optional; provides diff view)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the visualizer with:

```bash
python json_visualizer.py
```

Use the **Upload JSON File(s)** button to load one or two configuration files. When two files are provided, a comparison tab will display the differences.

## License

This project is released under the MIT License.

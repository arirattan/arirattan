"""JSON Configuration Visualizer for OCS settings.

This script provides a GUI to inspect one or two JSON files side by side. It
shows each configuration section in a tab with optional descriptions and offers
a search bar for quick navigation. When two files are loaded, a diff view is
created to highlight their differences.
"""

import json
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from tooltip import SECTION_TOOLTIPS, Tooltip

try:
    import darkdetect
except Exception:  # pragma: no cover - optional dependency
    darkdetect = None

try:
    from jsondiff import diff
except Exception:
    diff = None  # Diff functionality disabled if jsondiff is not installed




class JSONVisualizerApp:
    """Tkinter application to visualize JSON configuration files."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JSON Configuration Visualizer (OCS)")
        self.root.geometry("1100x700")

        # Increase default font size for readability
        default_font = tkfont.nametofont("TkDefaultFont")
        text_font = tkfont.nametofont("TkTextFont")
        default_font.configure(size=12)
        text_font.configure(size=12)

        # List of dicts: {'name': filename, 'data': json_data}
        self.files: list[dict] = []
        self.current_tabs: dict[str, tuple[tk.Canvas, ttk.Frame]] = {}
        self.search_results: list[tuple[str, str]] = []
        self.all_entries: list[ttk.Entry] = []
        self.tree_paths: dict[str, str] = {}

        # Lazy-load bookkeeping
        self.tab_json: dict[str, dict] = {}
        self.tab_frames: dict[str, ttk.Frame] = {}
        self.tab_initialized: set[str] = set()

        style = ttk.Style(self.root)
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
            elif "vista" in style.theme_names():
                style.theme_use("vista")
            elif "xpnative" in style.theme_names():
                style.theme_use("xpnative")
            else:
                style.theme_use(style.theme_use())
        except Exception:
            pass

        self.dark_mode = False
        if darkdetect is not None:
            try:
                self.dark_mode = darkdetect.theme().lower() == "dark"
            except Exception:
                pass

        self.theme_button = ttk.Button(root, text="Toggle Dark Mode", command=self.toggle_theme)
        self.theme_button.pack(pady=5)
        self.apply_theme()

        self.upload_button = ttk.Button(root, text="Upload JSON File(s)", command=self.load_files)
        self.upload_button.pack(pady=10)

        # Main paned window with navigation tree on the left
        self.paned = ttk.PanedWindow(root, orient="horizontal", sashrelief="raised")
        self.paned.pack(fill="both", expand=True)

        # Treeview for navigation
        self.tree_frame = ttk.Frame(self.paned)
        self.tree = ttk.Treeview(self.tree_frame, show="tree")
        self.tree.pack(fill="both", expand=True, side="left")
        tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.paned.add(self.tree_frame, weight=1)

        # Right frame contains search and notebook
        self.main_frame = ttk.Frame(self.paned)
        self.paned.add(self.main_frame, weight=4)

        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.pack(fill="x", padx=10)
        ttk.Label(self.search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        self.search_button = ttk.Button(self.search_frame, text="Go", command=self.perform_search)
        self.search_button.pack(side="left", padx=(5, 0))

        self.results_listbox = tk.Listbox(self.main_frame, height=5)
        self.results_listbox.pack(fill="x", padx=10)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_result_select)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.info_label = ttk.Label(self.main_frame, text="Please upload one or more JSON files to begin.")
        self.info_label.pack(pady=5)

    # ---------------------------
    # Theming
    # ---------------------------
    def apply_theme(self) -> None:
        """Apply light or dark color scheme."""
        if self.dark_mode:
            colors = {
                "background": "#2e2e2e",
                "foreground": "#ffffff",
                "activeBackground": "#444444",
                "activeForeground": "#ffffff",
            }
        else:
            colors = {
                "background": "#f0f0f0",
                "foreground": "#000000",
                "activeBackground": "#d9d9d9",
                "activeForeground": "#000000",
            }
        self.root.tk_setPalette(**colors)

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    # ---------------------------
    # File Handling
    # ---------------------------
    def load_files(self) -> None:
        """Open a file dialog and load selected JSON files."""
        file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        if not file_paths:
            return

        self.files.clear()
        self.current_tabs.clear()
        self.all_entries.clear()
        self.tree.delete(*self.tree.get_children())
        self.tree_paths.clear()
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.results_listbox.delete(0, tk.END)
        self.search_var.set("")
        self.search_results.clear()

        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                filename = os.path.basename(path)
                self.files.append({"name": filename, "data": data})
            except Exception as exc:  # pragma: no cover - GUI feedback
                messagebox.showerror("Error", f"Failed to load {path}: {exc}")
                return

        self.update_view()

    def update_view(self) -> None:
        """Clear existing tabs and display loaded files."""
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.current_tabs.clear()
        self.results_listbox.delete(0, tk.END)
        self.search_var.set("")
        self.search_results.clear()
        self.all_entries.clear()

        self.info_label.config(text="")

        if len(self.files) == 1:
            self.display_tabs(self.files[0]["data"], self.files[0]["name"])
        elif len(self.files) >= 2:
            self.display_tabs(self.files[0]["data"], self.files[0]["name"])
            self.display_comparison(
                base_data=self.files[0]["data"],
                base_name=self.files[0]["name"],
                compare_data=self.files[1]["data"],
                compare_name=self.files[1]["name"],
            )
            self.display_heatmap()

    # ---------------------------
    # Display Helpers
    # ---------------------------
    def display_tabs(self, data: dict, filename: str) -> None:
        self.tab_json.clear()
        self.tab_frames.clear()
        self.tab_initialized.clear()
        self.tree.delete(*self.tree.get_children())
        self.tree_paths.clear()

        for key, value in data.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=key)
            ttk.Label(frame, text="Select tab to load...").pack()
            self.tab_json[key] = value
            self.tab_frames[key] = frame
            root_id = self.tree.insert("", "end", text=key, open=False)
            self.tree_paths[root_id] = key
            self.build_tree_nodes(value, parent_item=root_id, path_prefix=key)

        def _init_first() -> None:
            event = tk.Event()
            event.widget = self.notebook
            self.on_tab_changed(event)

        self.root.after_idle(_init_first)

    def build_tree_nodes(self, data, parent_item: str, path_prefix: str) -> None:
        """Recursively populate the navigation tree."""
        if isinstance(data, dict):
            for k, v in data.items():
                node_path = f"{path_prefix}.{k}" if path_prefix else k
                item = self.tree.insert(parent_item, "end", text=k, open=False)
                self.tree_paths[item] = node_path
                self.build_tree_nodes(v, item, node_path)
        elif isinstance(data, list):
            for idx, item_data in enumerate(data):
                node_path = f"{path_prefix}[{idx}]"
                item = self.tree.insert(parent_item, "end", text=f"[{idx}]", open=False)
                self.tree_paths[item] = node_path
                self.build_tree_nodes(item_data, item, node_path)

    def build_nested_frame(
        self,
        parent: ttk.Frame,
        data,
        canvas: tk.Canvas | None = None,
        indent: int = 0,
        key_name: str | None = None,
        path_prefix: str = "",
    ) -> None:
        """Recursively render nested data structures."""
        if isinstance(data, dict):
            obj_label = key_name if key_name else "Object"
            frame = ttk.LabelFrame(parent, text=obj_label, padding=10)
            frame.pack(fill="x", padx=indent * 20 + 10, pady=5, anchor="nw")

            if path_prefix in SECTION_TOOLTIPS:
                Tooltip(frame, SECTION_TOOLTIPS[path_prefix])

            for k, v in data.items():
                new_path = f"{path_prefix}.{k}" if path_prefix else k
                self.build_nested_frame(
                    frame, v, canvas=canvas, indent=indent + 1, key_name=k, path_prefix=new_path
                )
        elif isinstance(data, list):
            list_label = f"{key_name} [List]" if key_name else "List"
            frame = ttk.LabelFrame(parent, text=list_label, padding=10)
            frame.pack(fill="x", padx=indent * 20 + 10, pady=5, anchor="nw")

            if path_prefix in SECTION_TOOLTIPS:
                Tooltip(frame, SECTION_TOOLTIPS[path_prefix])

            for idx, item in enumerate(data):
                new_path = f"{path_prefix}[{idx}]"
                self.build_nested_frame(
                    frame,
                    item,
                    canvas=canvas,
                    indent=indent + 1,
                    key_name=f"[{idx}]",
                    path_prefix=new_path,
                )
        else:
            row = ttk.Frame(parent)
            row.pack(fill="x", padx=indent * 20 + 10, pady=2, anchor="nw")
            display_key = key_name if key_name else str(data)
            label = ttk.Label(row, text=f"{display_key}:", width=30)
            label.pack(side="left")

            if path_prefix in SECTION_TOOLTIPS:
                Tooltip(label, SECTION_TOOLTIPS[path_prefix])

            entry = ttk.Entry(row)
            entry.insert(0, str(data))
            entry.pack(side="left", fill="x", expand=True)

            entry.full_path = path_prefix
            entry.parent_canvas = canvas
            entry.default_bg = entry.cget("background")
            self.all_entries.append(entry)

    # ---------------------------
    # Search
    # ---------------------------
    def perform_search(self) -> None:
        query = self.search_var.get().strip().lower()
        self.results_listbox.delete(0, tk.END)
        self.search_results.clear()

        for ent in self.all_entries:
            ent.config(background=ent.default_bg)

        if not query:
            return

        for tab_key, (canvas, scrollable) in self.current_tabs.items():
            for widget in scrollable.winfo_children():
                self.search_in_widget(widget, query, tab_key)

        for i, (tab_key, path) in enumerate(self.search_results):
            self.results_listbox.insert(i, f"{tab_key}: {path}")

    def search_in_widget(self, widget: tk.Widget, query: str, tab_key: str) -> None:
        if isinstance(widget, ttk.Entry):
            value = widget.get().lower()
            path = getattr(widget, "full_path", "")
            if query in value or query in path.lower():
                widget.config(background="yellow")
                self.search_results.append((tab_key, path))
        elif isinstance(widget, (ttk.Frame, ttk.LabelFrame)):
            for child in widget.winfo_children():
                self.search_in_widget(child, query, tab_key)

    def on_tab_changed(self, event: tk.Event) -> None:
        """Lazy-load tab content when selected."""
        tab_id = event.widget.select()
        key = event.widget.tab(tab_id, "text")
        if key in self.tab_initialized:
            return
        frame = self.tab_frames.get(key)
        data = self.tab_json.get(key)
        if frame is None or data is None:
            return
        for child in frame.winfo_children():
            child.destroy()
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind(
            "<Enter>",
            lambda e, c=canvas: c.bind_all(
                "<MouseWheel>", lambda ev: c.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            ),
        )
        canvas.bind("<Leave>", lambda e, c=canvas: c.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))

        self.build_nested_frame(scrollable_frame, data, canvas=canvas, path_prefix=key)
        self.current_tabs[key] = (canvas, scrollable_frame)
        self.tab_initialized.add(key)

    def on_result_select(self, event: tk.Event) -> None:
        if not self.search_results:
            return
        idx = self.results_listbox.curselection()[0]
        tab_key, path = self.search_results[idx]
        tab_index = list(self.current_tabs.keys()).index(tab_key)
        self.notebook.select(tab_index)
        canvas, scrollable = self.current_tabs[tab_key]
        self.scroll_to_path(scrollable, path)

    def on_tree_select(self, event: tk.Event) -> None:
        if not self.tree.selection():
            return
        item = self.tree.selection()[0]
        path = self.tree_paths.get(item)
        if not path:
            return
        tab_key = path.split(".")[0].split("[")[0]
        if tab_key not in self.current_tabs:
            return
        tab_index = list(self.current_tabs.keys()).index(tab_key)
        self.notebook.select(tab_index)
        if tab_key not in self.tab_initialized:
            fake_event = tk.Event()
            fake_event.widget = self.notebook
            self.on_tab_changed(fake_event)
        canvas, scrollable = self.current_tabs[tab_key]
        self.scroll_to_path(scrollable, path)

    def scroll_to_path(self, parent: ttk.Frame, path: str) -> None:
        for widget in parent.winfo_children():
            result = self.find_widget_by_path(widget, path)
            if result:
                widgets_y = result.winfo_rooty() - parent.winfo_rooty()
                parent_canvas = result.parent_canvas
                parent_canvas.yview_moveto(widgets_y / parent.winfo_height())
                result.focus()
                break

    def find_widget_by_path(self, widget: tk.Widget, path: str):
        if isinstance(widget, ttk.Entry) and getattr(widget, "full_path", "") == path:
            return widget
        if isinstance(widget, (ttk.Frame, ttk.LabelFrame)):
            for child in widget.winfo_children():
                found = self.find_widget_by_path(child, path)
                if found:
                    return found
        return None

    # ---------------------------
    # Diff View
    # ---------------------------
    def display_comparison(
        self,
        base_data: dict,
        base_name: str,
        compare_data: dict,
        compare_name: str,
    ) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Compare: {compare_name}")

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)
        text = tk.Text(text_frame, wrap="none")
        text.pack(fill="both", expand=True, side="left")

        text.bind(
            "<Enter>",
            lambda e, t=text: t.bind_all(
                "<MouseWheel>", lambda ev: t.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            ),
        )
        text.bind("<Leave>", lambda e, t=text: t.unbind_all("<MouseWheel>"))
        text.bind("<Button-4>", lambda e, t=text: t.yview_scroll(-1, "units"))
        text.bind("<Button-5>", lambda e, t=text: t.yview_scroll(1, "units"))

        v_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        v_scroll.pack(fill="y", side="right")
        text.configure(yscrollcommand=v_scroll.set)

        h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        h_scroll.pack(fill="x", side="bottom")
        text.configure(xscrollcommand=h_scroll.set)

        try:
            if diff is None:
                raise ImportError("jsondiff not available")
            delta = diff(base_data, compare_data, dump=True)
            diff_text = json.dumps(delta, indent=2)
        except Exception:
            diff_text = "Error generating diff or jsondiff not installed."
        text.insert("1.0", diff_text)

    # ---------------------------
    # Heatmap View
    # ---------------------------
    def display_heatmap(self) -> None:
        if len(self.files) <= 1:
            return

        heat_win = tk.Toplevel(self.root)
        heat_win.title("Heatmap Comparison")
        heat_win.geometry("800x600")
        if hasattr(self, "apply_theme"):
            self.apply_theme()

        canvas = tk.Canvas(heat_win)
        canvas.pack(fill="both", expand=True, side="left")
        v_scroll = ttk.Scrollbar(heat_win, orient="vertical", command=canvas.yview)
        v_scroll.pack(fill="y", side="right")
        h_scroll = ttk.Scrollbar(heat_win, orient="horizontal", command=canvas.xview)
        h_scroll.pack(fill="x", side="bottom")
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        heat_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=heat_frame, anchor="nw")
        heat_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        keys = sorted({k for f in self.files for k in f["data"].keys()})
        base_data = self.files[0]["data"]

        matrix: list[list[int]] = []
        max_score = 0
        for key in keys:
            row = []
            for f in self.files[1:]:
                score = self.diff_count(base_data.get(key), f["data"].get(key))
                row.append(score)
                if score > max_score:
                    max_score = score
            matrix.append(row)

        cell = 25
        for col, f in enumerate(self.files[1:]):
            ttk.Label(heat_frame, text=f["name"], font=(None, 9, "bold")).grid(
                row=0, column=col + 1, padx=2, sticky="w"
            )
        for row_idx, key in enumerate(keys):
            ttk.Label(heat_frame, text=key, font=(None, 9, "bold")).grid(
                row=row_idx + 1, column=0, pady=2, sticky="e"
            )
            for col_idx, score in enumerate(matrix[row_idx]):
                if max_score:
                    intensity = int(min(score / max_score, 1) * 255)
                else:
                    intensity = 0
                red = 255
                green_blue = 255 - intensity
                color = f"#{red:02x}{green_blue:02x}{green_blue:02x}"
                frame = tk.Frame(
                    heat_frame, background=color, width=cell, height=cell, borderwidth=1, relief="solid"
                )
                frame.grid(row=row_idx + 1, column=col_idx + 1)

    def diff_count(self, a, b) -> int:
        if a is None and b is None:
            return 0
        if isinstance(a, dict) and isinstance(b, dict):
            keys = set(a.keys()) | set(b.keys())
            return sum(self.diff_count(a.get(k), b.get(k)) for k in keys)
        if isinstance(a, list) and isinstance(b, list):
            length = max(len(a), len(b))
            return sum(
                self.diff_count(a[i] if i < len(a) else None, b[i] if i < len(b) else None)
                for i in range(length)
            )
        return 0 if a == b else 1


if __name__ == "__main__":  # pragma: no cover - GUI code
    root = tk.Tk()
    app = JSONVisualizerApp(root)
    root.mainloop()


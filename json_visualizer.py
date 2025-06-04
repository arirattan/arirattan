"""JSON Configuration Visualizer for OCS settings.

This script provides a GUI to inspect one or two JSON files side by side. It
shows each configuration section in a tab with optional descriptions and offers
a search bar for quick navigation. When two files are loaded, a diff view is
created to highlight their differences.
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from jsondiff import diff
except Exception:
    diff = None  # Diff functionality disabled if jsondiff is not installed


# ----------------------------
# TOOLTIP HELPER CLASS
# ----------------------------
class Tooltip:
    """Display a tooltip when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=(None, 9),
        )
        label.pack(ipadx=4, ipady=2)

    def hide(self, event: tk.Event | None = None) -> None:
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


# ----------------------------
# SECTION TOOLTIPS DICTIONARY
# ----------------------------
SECTION_TOOLTIPS = {
    "secureme-language": "Localization settings for the Secure.me Web SDK (e.g. text, error messages).",
    "shared": "Shared configuration across multiple services (common endpoints, timeouts, etc.).",
    "secureme": "Secure.me Web SDK settings—controls how the Web SDK behaves (session options, tags).",
    "mobilesdk": "Mobile SDK configuration (API keys, callbacks, device checks).",
    "bos": "Business Object Service (BOS) settings—used for backend orchestration.",
    "outbox": "Outbox queue settings (delivery retries, backoff, endpoints).",
    "instinct": "Instinct fraud detection settings (thresholds, API endpoints).",
    "mobiledemo": "Demo/sample configuration for mobile implementations.",
    "edv": "EDV (Electronic Data Vault) settings—controls secure storage options.",
    "riskmanager": "Risk Manager settings (risk thresholds, actions on high-risk).",
    "doublecheck": "Double-check (secondary review) service settings (timing, rules).",
    "bv": "Business Verification settings (e.g. fuzzy logic, ID length).",
    "checksscan": "Check/scan service settings (scan types, parameters).",
    "console": "Console display settings—UI flags, toggle options in the console.",
    "eds": "EDS (Electronic Document Service) settings—document handling rules.",
    "media": "Media (image/video) processing settings (compression, endpoints).",
    "phone-email-verification": "Phone and email verification service settings (OTP length, timeout).",
    "sdc": "Serial Fraud Monitor (SFM) / SDC settings (address repetition, bot detection).",
    "users": "User management settings—roles, session timeouts.",
    "aml": "Anti-Money Laundering (AML) settings (watchlists, thresholds).",
    "pii": "PII (Personally Identifiable Information) handling settings (masking, retention).",
    "eid": "eID (Electronic ID) verification settings—supported formats, endpoints.",
    "webapp": "WebApp integration settings—CORS, CSP, callback URLs.",
    "workflow": "Workflow definitions—sequence of services to run, retry logic.",
    "policy": "Policy manager settings—rule definitions, activation toggles.",
    "biometrics": "Biometrics service settings (face match thresholds, liveness).",
}


class JSONVisualizerApp:
    """Tkinter application to visualize JSON configuration files."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JSON Configuration Visualizer (OCS)")
        self.root.geometry("1000x700")

        # List of dicts: {'name': filename, 'data': json_data}
        self.files: list[dict] = []
        self.current_tabs: dict[str, tuple[tk.Canvas, ttk.Frame]] = {}
        self.search_results: list[tuple[str, str]] = []
        self.all_entries: list[ttk.Entry] = []

        style = ttk.Style(self.root)
        try:
            style.theme_use(style.theme_use())
        except Exception:
            pass

        self.upload_button = ttk.Button(root, text="Upload JSON File(s)", command=self.load_files)
        self.upload_button.pack(pady=10)

        self.search_frame = ttk.Frame(root)
        self.search_frame.pack(fill="x", padx=10)
        ttk.Label(self.search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        self.search_button = ttk.Button(self.search_frame, text="Go", command=self.perform_search)
        self.search_button.pack(side="left", padx=(5, 0))

        self.results_listbox = tk.Listbox(root, height=5)
        self.results_listbox.pack(fill="x", padx=10)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_result_select)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.info_label = ttk.Label(root, text="Please upload one or more JSON files to begin.")
        self.info_label.pack(pady=5)

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

    # ---------------------------
    # Display Helpers
    # ---------------------------
    def display_tabs(self, data: dict, filename: str) -> None:
        for key, value in data.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=key)
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
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

            self.build_nested_frame(scrollable_frame, value, canvas=canvas, path_prefix=key)

            self.current_tabs[key] = (canvas, scrollable_frame)

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

    def on_result_select(self, event: tk.Event) -> None:
        if not self.search_results:
            return
        idx = self.results_listbox.curselection()[0]
        tab_key, path = self.search_results[idx]
        tab_index = list(self.current_tabs.keys()).index(tab_key)
        self.notebook.select(tab_index)
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


if __name__ == "__main__":  # pragma: no cover - GUI code
    root = tk.Tk()
    app = JSONVisualizerApp(root)
    root.mainloop()


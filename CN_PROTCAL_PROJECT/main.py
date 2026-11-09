
import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from protocols import simulate_protocol
from visualization import show_animation


# =========================================================
# NETPULSE THEME
# =========================================================

BG = "#F6F5F2"
SIDEBAR = "#FFFFFF"
PANEL = "#FFFFFF"
SOFT = "#F0EFEB"
BORDER = "#E4E1DB"
TEXT = "#30343B"
MUTED = "#727780"

CORAL = "#F07858"
CORAL_DARK = "#D85E41"
CORAL_PALE = "#FFF0EA"
GREEN = "#328365"
GREEN_PALE = "#E8F5EE"
SAGE = "#8B9B86"
AMBER = "#B77A20"
RED = "#C84F4F"

PROTOCOLS = [
    "One-Bit Sliding Window",
    "Go-Back-N",
    "Selective Repeat"
]

SHORT_NAMES = {
    "One-Bit Sliding Window": "One-Bit",
    "Go-Back-N": "Go-Back-N",
    "Selective Repeat": "Selective"
}

PROTOCOL_COLORS = {
    "One-Bit Sliding Window": CORAL,
    "Go-Back-N": SAGE,
    "Selective Repeat": AMBER
}

DEFAULTS = {
    "Window Size": "4",
    "Number of Frames": "10",
    "Transmission Delay (ms)": "100",
    "ACK Delay (ms)": "50",
    "Packet Loss (%)": "10",
    "ACK Loss (%)": "5",
    "Timeout (ms)": "300"
}

results_by_protocol = {}
last_result = None
last_protocol = None
last_events = []


# =========================================================
# ROOT WINDOW AND STYLES
# =========================================================

root = tk.Tk()
root.title("NETPULSE | Network Protocol Simulator")
root.geometry("1440x900")
root.minsize(1050, 700)
root.configure(bg=BG)

try:
    root.state("zoomed")
except tk.TclError:
    pass

style = ttk.Style(root)
style.theme_use("clam")

style.configure(
    "TCombobox",
    fieldbackground=PANEL,
    background=SOFT,
    foreground=TEXT,
    padding=6
)

style.map(
    "TCombobox",
    fieldbackground=[("readonly", PANEL)],
    foreground=[("readonly", TEXT)]
)

style.configure(
    "TNotebook",
    background=BG,
    borderwidth=0,
    tabmargins=(0, 0, 0, 0)
)

style.configure(
    "TNotebook.Tab",
    background=SOFT,
    foreground=MUTED,
    padding=(14, 9),
    font=("Segoe UI", 9, "bold")
)

style.map(
    "TNotebook.Tab",
    background=[("selected", CORAL_PALE)],
    foreground=[("selected", CORAL_DARK)]
)

style.configure(
    "Treeview",
    background=PANEL,
    fieldbackground=PANEL,
    foreground=TEXT,
    rowheight=30,
    borderwidth=0,
    font=("Segoe UI", 9)
)

style.configure(
    "Treeview.Heading",
    background=SOFT,
    foreground=TEXT,
    padding=7,
    font=("Segoe UI", 9, "bold")
)

style.map(
    "Treeview",
    background=[("selected", CORAL_PALE)],
    foreground=[("selected", TEXT)]
)


# =========================================================
# UI HELPERS
# =========================================================

def label(parent, text, size=10, color=TEXT,
          bold=False, bg=None, **kwargs):
    return tk.Label(
        parent,
        text=text,
        font=("Segoe UI", size, "bold" if bold else "normal"),
        bg=bg or BG,
        fg=color,
        **kwargs
    )


def make_panel(parent):
    return tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )


def make_button(parent, text, command, primary=False):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=CORAL if primary else PANEL,
        fg="white" if primary else TEXT,
        activebackground=CORAL_DARK if primary else SOFT,
        activeforeground="white" if primary else TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=CORAL if primary else BORDER,
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=9,
        cursor="hand2"
    )


def fmt(value, digits=2):
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


# =========================================================
# MAIN LAYOUT
# =========================================================

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

sidebar = tk.Frame(
    root,
    bg=SIDEBAR,
    width=235,
    highlightbackground=BORDER,
    highlightthickness=1
)
sidebar.grid(row=0, column=0, sticky="ns")
sidebar.grid_propagate(False)

workspace = tk.Frame(root, bg=BG)
workspace.grid(
    row=0, column=1, sticky="nsew",
    padx=20, pady=15
)

workspace.grid_columnconfigure(0, weight=1)
workspace.grid_rowconfigure(2, weight=1)


# =========================================================
# SIDEBAR
# =========================================================

brand = tk.Frame(sidebar, bg=SIDEBAR)
brand.pack(fill="x", padx=19, pady=(25, 28))

label(
    brand, "◇  NETPULSE",
    size=20, color=CORAL, bold=True, bg=SIDEBAR
).pack(anchor="w")

label(
    brand, "COMPUTER NETWORKS LAB",
    size=9, color=MUTED, bold=True, bg=SIDEBAR
).pack(anchor="w", pady=(7, 0))

label(
    sidebar, "WORKSPACE",
    size=9, color=MUTED, bold=True, bg=SIDEBAR
).pack(anchor="w", padx=20, pady=(0, 10))

sidebar_buttons = {}


def set_active_sidebar(key):
    for name, widget in sidebar_buttons.items():
        active = name == key
        widget.configure(
            bg=CORAL_PALE if active else SIDEBAR,
            fg=CORAL_DARK if active else TEXT
        )


def add_sidebar_button(key, text, command):
    widget = tk.Button(
        sidebar,
        text=text,
        command=command,
        anchor="w",
        padx=14,
        pady=12,
        bg=SIDEBAR,
        fg=TEXT,
        activebackground=CORAL_PALE,
        activeforeground=CORAL_DARK,
        relief="flat",
        bd=0,
        font=("Segoe UI", 9, "bold"),
        cursor="hand2"
    )
    widget.pack(fill="x", padx=9, pady=3)
    sidebar_buttons[key] = widget


sidebar_footer = tk.Frame(sidebar, bg=SIDEBAR)
sidebar_footer.pack(side="bottom", fill="x", padx=20, pady=20)

tk.Frame(
    sidebar_footer, bg=BORDER, height=1
).pack(fill="x", pady=(0, 12))

label(
    sidebar_footer, "SIMULATOR STATUS",
    size=9, color=MUTED, bold=True, bg=SIDEBAR
).pack(anchor="w")

status_label = label(
    sidebar_footer, "●  Ready to simulate",
    size=9, color=GREEN, bold=True, bg=SIDEBAR
)
status_label.pack(anchor="w", pady=(8, 0))


# =========================================================
# HEADER
# =========================================================

header = tk.Frame(workspace, bg=BG)
header.grid(row=0, column=0, sticky="ew", pady=(0, 13))
header.grid_columnconfigure(0, weight=1)

header_left = tk.Frame(header, bg=BG)
header_left.grid(row=0, column=0, sticky="w")

label(
    header_left, "Network Protocol Simulator",
    size=22, color=TEXT, bold=True, bg=BG
).pack(anchor="w")

label(
    header_left,
    "Configure, simulate and compare reliable data transfer.",
    size=10, color=MUTED, bg=BG
).pack(anchor="w", pady=(5, 0))

tk.Label(
    header,
    text="●  LOCAL SIMULATION",
    font=("Segoe UI", 9, "bold"),
    bg=GREEN_PALE,
    fg=GREEN,
    padx=11,
    pady=7
).grid(row=0, column=1, padx=4)


# =========================================================
# SIMULATION CONFIGURATION
# =========================================================

settings = make_panel(workspace)
settings.grid(row=1, column=0, sticky="ew", pady=(0, 12))

for column in (1, 3, 5):
    settings.grid_columnconfigure(column, weight=1)

label(
    settings, "SIMULATION CONFIGURATION",
    size=10, color=CORAL_DARK, bold=True, bg=PANEL
).grid(
    row=0, column=0, columnspan=6,
    sticky="w", padx=17, pady=(11, 5)
)

protocol_var = tk.StringVar(value="Go-Back-N")

label(
    settings, "Protocol", size=9, color=MUTED, bg=PANEL
).grid(row=1, column=0, sticky="w", padx=17, pady=6)

protocol_box = ttk.Combobox(
    settings,
    textvariable=protocol_var,
    values=PROTOCOLS,
    state="readonly",
    width=23
)
protocol_box.grid(
    row=1, column=1, sticky="ew",
    padx=(0, 15), pady=6
)

entries = {}

for index, (name, default) in enumerate(DEFAULTS.items()):
    row = 2 + index // 3
    group = index % 3
    label_col = group * 2
    entry_col = label_col + 1

    label(
        settings, name, size=9, color=MUTED, bg=PANEL
    ).grid(
        row=row, column=label_col,
        sticky="w", padx=17, pady=5
    )

    entry = ttk.Entry(settings, width=12)
    entry.insert(0, default)
    entry.grid(
        row=row, column=entry_col,
        sticky="ew", padx=(0, 15), pady=5
    )
    entries[name] = entry


def on_protocol_change(event=None):
    """Keep the window size valid when the selected protocol changes."""
    selected_protocol = protocol_var.get()
    window_entry = entries["Window Size"]

    if selected_protocol == "One-Bit Sliding Window":
        window_entry.delete(0, tk.END)
        window_entry.insert(0, "1")
    else:
        # Restore the standard default when leaving the one-bit protocol.
        window_entry.delete(0, tk.END)
        window_entry.insert(0, DEFAULTS["Window Size"])


protocol_box.bind("<<ComboboxSelected>>", on_protocol_change)


# =========================================================
# TABS
# =========================================================

tabs = ttk.Notebook(workspace)
tabs.grid(row=2, column=0, sticky="nsew")

dashboard_tab = tk.Frame(tabs, bg=BG)
results_tab = tk.Frame(tabs, bg=BG)
comparison_tab = tk.Frame(tabs, bg=BG)

tabs.add(dashboard_tab, text="  Dashboard  ")
tabs.add(results_tab, text="  Protocol Results  ")
tabs.add(comparison_tab, text="  Protocol Comparison  ")

dashboard_tab.grid_columnconfigure(0, weight=1)
dashboard_tab.grid_rowconfigure(1, weight=1)

results_tab.grid_columnconfigure(0, weight=1)
results_tab.grid_rowconfigure(0, weight=1)

comparison_tab.grid_columnconfigure(0, weight=1)
comparison_tab.grid_rowconfigure(0, weight=1)


# =========================================================
# KPI CARDS
# =========================================================

cards_frame = tk.Frame(dashboard_tab, bg=BG)
cards_frame.grid(row=0, column=0, sticky="ew", pady=(11, 13))

for column in range(4):
    cards_frame.grid_columnconfigure(
        column, weight=1, uniform="kpi"
    )

card_values = {}


def create_card(column, title, key, accent):
    card = make_panel(cards_frame)
    card.grid(
        row=0, column=column, sticky="ew",
        padx=(0, 8) if column < 3 else 0
    )

    tk.Frame(card, bg=accent, height=4).pack(fill="x")

    body = tk.Frame(card, bg=PANEL)
    body.pack(fill="both", expand=True, padx=14, pady=11)

    label(
        body, title.upper(), size=8,
        color=MUTED, bold=True, bg=PANEL
    ).pack(anchor="w")

    value_label = label(
        body, "—", size=18,
        color=accent, bold=True, bg=PANEL
    )
    value_label.pack(anchor="w", pady=(7, 0))

    card_values[key] = value_label


create_card(0, "Frames delivered", "delivered", CORAL)
create_card(1, "Retransmissions", "retransmissions", AMBER)
create_card(2, "Throughput", "throughput", GREEN)
create_card(3, "Simulation status", "status", GREEN)


# =========================================================
# DASHBOARD PERFORMANCE OVERVIEW
# =========================================================

dashboard_lower = tk.Frame(dashboard_tab, bg=BG)
dashboard_lower.grid(row=1, column=0, sticky="nsew")

dashboard_lower.grid_columnconfigure(0, weight=3)
dashboard_lower.grid_columnconfigure(1, weight=2)
dashboard_lower.grid_rowconfigure(0, weight=1)

performance_panel = make_panel(dashboard_lower)
performance_panel.grid(
    row=0, column=0, sticky="nsew", padx=(0, 8)
)

performance_panel.grid_columnconfigure(0, weight=1)
performance_panel.grid_rowconfigure(1, weight=1)

label(
    performance_panel, "PERFORMANCE OVERVIEW",
    size=10, color=CORAL_DARK, bold=True, bg=PANEL
).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

performance_figure = Figure(
    figsize=(7, 4),
    dpi=100,
    facecolor=PANEL
)

performance_axes = [
    performance_figure.add_subplot(311),
    performance_figure.add_subplot(312),
    performance_figure.add_subplot(313)
]

performance_figure.subplots_adjust(
    left=0.32,
    right=0.94,
    top=0.92,
    bottom=0.16,
    hspace=1.35
)

performance_canvas = FigureCanvasTkAgg(
    performance_figure, master=performance_panel
)

performance_canvas.get_tk_widget().grid(
    row=1, column=0, sticky="nsew",
    padx=8, pady=(0, 8)
)


# =========================================================
# SIMULATION CONTROL PANEL
# =========================================================

control_panel = make_panel(dashboard_lower)
control_panel.grid(row=0, column=1, sticky="nsew")

label(
    control_panel, "SIMULATION CONTROL",
    size=10, color=CORAL_DARK, bold=True, bg=PANEL
).pack(anchor="w", padx=15, pady=(15, 8))

tk.Label(
    control_panel,
    text="Run a protocol, compare all methods, or watch data transmission.",
    font=("Segoe UI", 9),
    bg=PANEL,
    fg=MUTED,
    justify="left",
    anchor="w",
    wraplength=250
).pack(fill="x", padx=15, pady=(0, 12))


# =========================================================
# RESULTS TABLE TAB
# =========================================================

table_panel = make_panel(results_tab)
table_panel.grid(
    row=0, column=0, sticky="nsew",
    padx=4, pady=10
)

table_panel.grid_columnconfigure(0, weight=1)
table_panel.grid_rowconfigure(1, weight=1)

label(
    table_panel, "PROTOCOL RESULTS",
    size=11, color=CORAL_DARK, bold=True, bg=PANEL
).grid(row=0, column=0, sticky="w", padx=16, pady=12)

table_wrap = tk.Frame(table_panel, bg=PANEL)
table_wrap.grid(
    row=1, column=0, sticky="nsew",
    padx=10, pady=(0, 10)
)

table_wrap.grid_columnconfigure(0, weight=1)
table_wrap.grid_rowconfigure(0, weight=1)

columns = (
    "protocol", "transmitted", "retransmissions",
    "lost", "acks", "delivered", "time",
    "throughput", "efficiency", "completed"
)

headings = {
    "protocol": "Protocol",
    "transmitted": "Transmitted",
    "retransmissions": "Retransmissions",
    "lost": "Packets Lost",
    "acks": "ACKs Received",
    "delivered": "Delivered",
    "time": "Time (ms)",
    "throughput": "Throughput",
    "efficiency": "Efficiency (%)",
    "completed": "Completed"
}

column_widths = {
    "protocol": 170,
    "transmitted": 90,
    "retransmissions": 110,
    "lost": 90,
    "acks": 100,
    "delivered": 85,
    "time": 100,
    "throughput": 95,
    "efficiency": 105,
    "completed": 90
}

tree = ttk.Treeview(
    table_wrap,
    columns=columns,
    show="headings",
    height=8
)

for column in columns:
    tree.heading(column, text=headings[column], anchor="center")
    tree.column(
        column,
        width=column_widths[column],
        minwidth=65,
        anchor="center",
        stretch=True
    )

tree.column("protocol", anchor="w", minwidth=145)

tree_y_scroll = ttk.Scrollbar(
    table_wrap, orient="vertical", command=tree.yview
)
tree_x_scroll = ttk.Scrollbar(
    table_wrap, orient="horizontal", command=tree.xview
)

tree.configure(
    yscrollcommand=tree_y_scroll.set,
    xscrollcommand=tree_x_scroll.set
)

tree.grid(row=0, column=0, sticky="nsew")
tree_y_scroll.grid(row=0, column=1, sticky="ns")
tree_x_scroll.grid(row=1, column=0, sticky="ew")


# =========================================================
# COMPARISON CHARTS TAB
# =========================================================

comparison_panel = make_panel(comparison_tab)
comparison_panel.grid(
    row=0, column=0, sticky="nsew",
    padx=4, pady=10
)

comparison_panel.grid_columnconfigure(0, weight=1)
comparison_panel.grid_rowconfigure(1, weight=1)

label(
    comparison_panel, "PROTOCOL PERFORMANCE COMPARISON",
    size=11, color=CORAL_DARK, bold=True, bg=PANEL
).grid(row=0, column=0, sticky="w", padx=16, pady=12)

comparison_figure = Figure(
    figsize=(13, 5.5),
    dpi=100,
    facecolor=PANEL,
    constrained_layout=True
)

# Three equally sized axes prevent the right-most chart from being clipped.
comparison_axes = comparison_figure.subplots(1, 3, squeeze=False)[0]

comparison_figure.set_constrained_layout_pads(
    w_pad=0.35,
    h_pad=0.30,
    wspace=0.22,
    hspace=0.10
)

comparison_canvas = FigureCanvasTkAgg(
    comparison_figure, master=comparison_panel
)

comparison_canvas.get_tk_widget().grid(
    row=1, column=0, sticky="nsew",
    padx=10, pady=(0, 10)
)


# =========================================================
# INPUT VALIDATION
# =========================================================

def get_settings(protocol):
    values = {}

    integer_fields = {
        "Window Size",
        "Number of Frames",
        "Transmission Delay (ms)",
        "ACK Delay (ms)",
        "Timeout (ms)"
    }

    for name, entry in entries.items():
        raw = entry.get().strip()

        if not raw:
            raise ValueError(f"{name} cannot be empty.")

        try:
            number = float(raw)
        except ValueError:
            raise ValueError(f"{name} must be numeric.")

        if name in integer_fields:
            if not number.is_integer():
                raise ValueError(f"{name} must be a whole number.")
            number = int(number)

        values[name] = number

    if values["Window Size"] < 1:
        raise ValueError("Window size must be at least 1.")

    if not 1 <= values["Number of Frames"] <= 500:
        raise ValueError("Number of frames must be between 1 and 500.")

    if values["Transmission Delay (ms)"] <= 0:
        raise ValueError("Transmission delay must be positive.")

    if values["ACK Delay (ms)"] < 0:
        raise ValueError("ACK delay cannot be negative.")

    if values["Timeout (ms)"] <= 0:
        raise ValueError("Timeout must be positive.")

    for name in ("Packet Loss (%)", "ACK Loss (%)"):
        if not 0 <= values[name] <= 100:
            raise ValueError(f"{name} must be between 0 and 100.")

    if protocol == "One-Bit Sliding Window":
        values["Window Size"] = 1

    return values


# =========================================================
# PERFORMANCE OVERVIEW WITH NUMBERED AXES
# =========================================================

def draw_performance_metric(ax, title, value, color, formatter):
    ax.clear()
    ax.set_facecolor(PANEL)

    try:
        value = max(0.0, float(value))
    except (TypeError, ValueError):
        value = 0.0

    if "efficiency" in title.lower():
        maximum = 100.0
    else:
        maximum = max(value * 1.25, 1.0)

    ax.barh(
        [0],
        [value],
        height=0.34,
        color=color,
        zorder=3
    )

    ax.set_xlim(0, maximum)
    ax.set_ylim(-0.65, 0.65)

    # Metric name on the left.
    ax.set_yticks([0])
    ax.set_yticklabels(
        [title],
        fontsize=8,
        fontweight="bold",
        color=TEXT
    )
    ax.tick_params(axis="y", length=0, pad=8)

    # Numbered horizontal scale.
    ticks = [
        maximum * 0.0,
        maximum * 0.25,
        maximum * 0.50,
        maximum * 0.75,
        maximum
    ]

    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [f"{tick:g}" for tick in ticks],
        fontsize=7,
        color=MUTED
    )
    ax.tick_params(
        axis="x",
        bottom=True,
        labelbottom=True,
        length=3,
        pad=3,
        colors=MUTED
    )

    ax.grid(
        axis="x",
        linestyle="--",
        linewidth=0.5,
        color=BORDER,
        zorder=0
    )
    ax.set_axisbelow(True)

    # Exact value at the end of the bar.
    label_x = min(
        value + maximum * 0.025,
        maximum * 0.76
    )

    ax.text(
        label_x,
        0,
        formatter(value),
        va="center",
        ha="left",
        fontsize=8,
        fontweight="bold",
        color=TEXT,
        clip_on=False
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BORDER)


def update_performance_chart():
    if last_result is None:
        metrics = [
            ("Throughput (frames/s)", 0, GREEN, lambda v: "—"),
            ("Delivery efficiency (%)", 0, SAGE, lambda v: "—"),
            ("Retransmissions", 0, CORAL, lambda v: "—")
        ]
    else:
        metrics = [
            (
                "Throughput (frames/s)",
                last_result.get("throughput_frames_per_second", 0),
                GREEN,
                lambda v: f"{v:.2f}"
            ),
            (
                "Delivery efficiency (%)",
                last_result.get("efficiency_percent", 0),
                SAGE,
                lambda v: f"{v:.2f}%"
            ),
            (
                "Retransmissions",
                last_result.get("retransmissions", 0),
                CORAL,
                lambda v: f"{v:.0f}"
            )
        ]

    for ax, metric in zip(performance_axes, metrics):
        draw_performance_metric(ax, *metric)

    performance_figure.subplots_adjust(
        left=0.32,
        right=0.94,
        top=0.92,
        bottom=0.16,
        hspace=1.35
    )

    performance_canvas.draw_idle()


# =========================================================
# PROTOCOL COMPARISON CHARTS
# =========================================================

def draw_comparison_metric(ax, protocols, values, title):
    ax.clear()
    ax.set_facecolor(PANEL)

    ax.set_title(
        title,
        fontsize=10,
        fontweight="bold",
        color=TEXT,
        pad=14
    )

    if not protocols:
        ax.text(
            0.5, 0.5,
            "Run a simulation",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=9,
            color=MUTED
        )
        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)
        return

    positions = list(range(len(protocols)))
    colors = [PROTOCOL_COLORS[p] for p in protocols]

    bars = ax.bar(
        positions,
        values,
        width=0.58,
        color=colors,
        zorder=3
    )

    ax.set_xticks(positions)
    ax.set_xticklabels(
        [SHORT_NAMES[p] for p in protocols],
        fontsize=8,
        color=MUTED
    )
    ax.tick_params(axis="x", pad=7)
    ax.tick_params(axis="y", labelsize=8, colors=MUTED)

    max_value = max([float(v) for v in values] + [1.0])
    ax.set_ylim(0, max_value * 1.25)

    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.5,
        color=BORDER
    )
    ax.set_axisbelow(True)

    ax.bar_label(
        bars,
        labels=[f"{float(v):.2f}" for v in values],
        fontsize=8,
        padding=4,
        color=TEXT
    )

    for spine in ax.spines.values():
        spine.set_color(BORDER)

    ax.margins(x=0.12)


def update_comparison_charts():
    protocols = list(results_by_protocol.keys())

    retransmissions = [
        results_by_protocol[p].get("retransmissions", 0)
        for p in protocols
    ]

    throughputs = [
        results_by_protocol[p].get("throughput_frames_per_second", 0)
        for p in protocols
    ]

    efficiencies = [
        results_by_protocol[p].get("efficiency_percent", 0)
        for p in protocols
    ]

    draw_comparison_metric(
        comparison_axes[0],
        protocols,
        retransmissions,
        "Retransmissions"
    )

    draw_comparison_metric(
        comparison_axes[1],
        protocols,
        throughputs,
        "Throughput"
    )

    draw_comparison_metric(
        comparison_axes[2],
        protocols,
        efficiencies,
        "Efficiency (%)"
    )

    comparison_figure.set_constrained_layout(True)
    comparison_figure.set_constrained_layout_pads(
        w_pad=0.35,
        h_pad=0.30,
        wspace=0.22,
        hspace=0.10
    )
    comparison_canvas.draw_idle()


def update_all_charts():
    update_performance_chart()
    update_comparison_charts()


# =========================================================
# RESULTS TABLE
# =========================================================

def refresh_results_table(protocol, result):
    values = (
        protocol,
        result.get("total_frames_transmitted", 0),
        result.get("retransmissions", 0),
        result.get("packets_lost", 0),
        result.get("acks_received", 0),
        result.get("successfully_delivered", 0),
        fmt(result.get("total_time_ms", 0)),
        fmt(result.get("throughput_frames_per_second", 0)),
        fmt(result.get("efficiency_percent", 0)),
        "Yes" if result.get("completed", False) else "No"
    )

    for item in tree.get_children():
        old_values = tree.item(item, "values")

        if old_values and old_values[0] == protocol:
            tree.item(item, values=values)
            return

    tree.insert("", tk.END, values=values)


# =========================================================
# DISPLAY SIMULATION RESULTS
# =========================================================

def display_results(protocol, result):
    global last_result, last_protocol, last_events

    results_by_protocol[protocol] = result
    last_result = result
    last_protocol = protocol
    last_events = result.get("event_log", [])

    delivered = result.get("successfully_delivered", 0)
    retransmissions = result.get("retransmissions", 0)
    throughput = result.get("throughput_frames_per_second", 0)
    completed = result.get("completed", False)

    configured_frames = result.get(
        "configured_num_frames",
        entries["Number of Frames"].get()
    )
    card_values["delivered"].configure(
        text=f"{delivered}/{configured_frames}"
    )
    card_values["retransmissions"].configure(text=str(retransmissions))
    card_values["throughput"].configure(text=fmt(throughput))
    card_values["status"].configure(
        text="COMPLETED" if completed else "INCOMPLETE",
        fg=GREEN if completed else RED
    )

    status_label.configure(
        text="●  Simulation completed" if completed
        else "●  Simulation incomplete",
        fg=GREEN if completed else RED
    )

    refresh_results_table(protocol, result)
    update_all_charts()


# =========================================================
# RUN ONE PROTOCOL
# =========================================================

def run_one(protocol):
    try:
        values = get_settings(protocol)

        status_label.configure(
            text="●  Simulation running...",
            fg=AMBER
        )
        root.update_idletasks()

        result = simulate_protocol(
            protocol=protocol,
            window_size=values["Window Size"],
            num_frames=values["Number of Frames"],
            transmission_delay=values["Transmission Delay (ms)"],
            ack_delay=values["ACK Delay (ms)"],
            packet_loss=values["Packet Loss (%)"],
            ack_loss=values["ACK Loss (%)"],
            timeout=values["Timeout (ms)"]
        )

        if not isinstance(result, dict):
            raise TypeError(
                "simulate_protocol() must return a dictionary."
            )

        required = [
            "total_frames_transmitted",
            "retransmissions",
            "packets_lost",
            "acks_received",
            "successfully_delivered",
            "total_time_ms",
            "throughput_frames_per_second",
            "efficiency_percent",
            "completed",
            "event_log"
        ]

        missing = [key for key in required if key not in result]

        if missing:
            raise KeyError(
                "Missing simulation fields: " + ", ".join(missing)
            )

        result["configured_num_frames"] = values["Number of Frames"]
        display_results(protocol, result)
        return result

    except Exception as error:
        status_label.configure(text="●  Simulation error", fg=RED)
        messagebox.showerror(
            "Simulation Error", str(error), parent=root
        )
        return None


def start_simulation():
    result = run_one(protocol_var.get())

    if result is not None:
        tabs.select(dashboard_tab)
        set_active_sidebar("dashboard")


# =========================================================
# COMPARE ALL PROTOCOLS
# =========================================================

def compare_all():
    try:
        values = get_settings("Go-Back-N")

        status_label.configure(
            text="●  Comparing protocols...",
            fg=AMBER
        )
        root.update_idletasks()

        new_results = {}

        for protocol in PROTOCOLS:
            result = simulate_protocol(
                protocol=protocol,
                window_size=(
                    1 if protocol == "One-Bit Sliding Window"
                    else values["Window Size"]
                ),
                num_frames=values["Number of Frames"],
                transmission_delay=values["Transmission Delay (ms)"],
                ack_delay=values["ACK Delay (ms)"],
                packet_loss=values["Packet Loss (%)"],
                ack_loss=values["ACK Loss (%)"],
                timeout=values["Timeout (ms)"]
            )

            if not isinstance(result, dict):
                raise TypeError(
                    f"{protocol} did not return a dictionary."
                )

            result["configured_num_frames"] = values["Number of Frames"]
            new_results[protocol] = result

        results_by_protocol.clear()
        results_by_protocol.update(new_results)

        for protocol, result in results_by_protocol.items():
            refresh_results_table(protocol, result)

        display_results(
            "Go-Back-N",
            results_by_protocol["Go-Back-N"]
        )

        status_label.configure(
            text="●  Comparison completed",
            fg=GREEN
        )

        tabs.select(comparison_tab)
        set_active_sidebar("comparison")

    except Exception as error:
        status_label.configure(text="●  Comparison error", fg=RED)
        messagebox.showerror(
            "Comparison Error", str(error), parent=root
        )


# =========================================================
# NETWORK ANIMATION
# =========================================================

def animate_simulation():
    if last_result is None or last_protocol is None:
        messagebox.showinfo(
            "No simulation",
            "Run a simulation first, then open the animation.",
            parent=root
        )
        return

    try:
        show_animation(
            root,
            last_protocol,
            int(entries["Number of Frames"].get()),
            last_events
        )
    except Exception as error:
        messagebox.showerror(
            "Animation Error", str(error), parent=root
        )


# =========================================================
# CLEAR RESULTS
# =========================================================

def clear_results():
    global last_result, last_protocol, last_events

    if results_by_protocol:
        confirm = messagebox.askyesno(
            "Clear Results",
            "Clear all simulation results?",
            parent=root
        )

        if not confirm:
            return

    results_by_protocol.clear()
    last_result = None
    last_protocol = None
    last_events = []

    for item in tree.get_children():
        tree.delete(item)

    card_values["delivered"].configure(text="—")
    card_values["retransmissions"].configure(text="—")
    card_values["throughput"].configure(text="—")
    card_values["status"].configure(text="—", fg=GREEN)

    status_label.configure(text="●  Ready to simulate", fg=GREEN)
    update_all_charts()


# =========================================================
# DASHBOARD ACTION BUTTONS
# =========================================================

make_button(
    control_panel,
    "▶  START SIMULATION",
    start_simulation,
    primary=True
).pack(fill="x", padx=14, pady=(4, 6))

make_button(
    control_panel,
    "⇄  COMPARE ALL PROTOCOLS",
    compare_all
).pack(fill="x", padx=14, pady=6)

make_button(
    control_panel,
    "▷  ANIMATE TRANSMISSION",
    animate_simulation
).pack(fill="x", padx=14, pady=6)

make_button(
    control_panel,
    "↺  CLEAR RESULTS",
    clear_results
).pack(fill="x", padx=14, pady=6)

tk.Frame(
    control_panel, bg=BORDER, height=1
).pack(fill="x", padx=14, pady=12)

label(
    control_panel, "QUICK TIP",
    size=9, color=AMBER, bold=True, bg=PANEL
).pack(anchor="w", padx=15)

tk.Label(
    control_panel,
    text="Increase packet loss or ACK loss to observe retransmissions and throughput changes.",
    font=("Segoe UI", 9),
    bg=PANEL,
    fg=MUTED,
    justify="left",
    anchor="w",
    wraplength=250
).pack(fill="x", padx=15, pady=(5, 14))


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

def open_dashboard():
    tabs.select(dashboard_tab)
    set_active_sidebar("dashboard")


def open_results():
    tabs.select(results_tab)
    set_active_sidebar("results")


def open_comparison():
    tabs.select(comparison_tab)
    set_active_sidebar("comparison")


def open_animation():
    animate_simulation()


add_sidebar_button("dashboard", "▦   Dashboard", open_dashboard)
add_sidebar_button("results", "▤   Protocol Results", open_results)
add_sidebar_button("comparison", "▥   Protocol Comparison", open_comparison)
add_sidebar_button("animation", "▷   Network Animation", open_animation)


def on_tab_change(event=None):
    selected = tabs.select()

    if selected == str(dashboard_tab):
        set_active_sidebar("dashboard")
    elif selected == str(results_tab):
        set_active_sidebar("results")
    else:
        set_active_sidebar("comparison")


tabs.bind("<<NotebookTabChanged>>", on_tab_change)


# =========================================================
# FOOTER
# =========================================================

label(
    workspace,
    "NETPULSE  •  One-Bit  •  Go-Back-N  •  Selective Repeat",
    size=9, color=MUTED, bg=BG
).grid(row=3, column=0, sticky="w", pady=(7, 0))


# =========================================================
# RESPONSIVE CHART SIZING
# =========================================================

def resize_performance(event):
    if event.width < 100 or event.height < 100:
        return

    dpi = performance_figure.get_dpi()

    performance_figure.set_size_inches(
        event.width / dpi,
        event.height / dpi,
        forward=False
    )

    performance_figure.subplots_adjust(
        left=0.32,
        right=0.94,
        top=0.92,
        bottom=0.16,
        hspace=1.35
    )

    performance_canvas.draw_idle()


def resize_comparison(event):
    if event.width < 100 or event.height < 100:
        return

    dpi = comparison_figure.get_dpi()

    comparison_figure.set_size_inches(
        event.width / dpi,
        event.height / dpi,
        forward=False
    )

    comparison_figure.set_constrained_layout(True)
    comparison_figure.set_constrained_layout_pads(
        w_pad=0.35,
        h_pad=0.30,
        wspace=0.22,
        hspace=0.10
    )
    comparison_canvas.draw_idle()


performance_canvas.get_tk_widget().bind(
    "<Configure>", resize_performance
)

comparison_canvas.get_tk_widget().bind(
    "<Configure>", resize_comparison
)


# =========================================================
# START APPLICATION
# =========================================================

update_all_charts()
set_active_sidebar("dashboard")
root.mainloop()

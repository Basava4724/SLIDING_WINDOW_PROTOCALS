import tkinter as tk
from tkinter import ttk, messagebox

BG = "#0b1220"
PANEL = "#111c2e"
TEXT = "#e5edf8"
MUTED = "#93a4bd"
BLUE = "#3b82f6"
GREEN = "#22c55e"
ORANGE = "#f59e0b"
RED = "#ef4444"
BORDER = "#263750"


def show_animation(root, protocol, num_frames, event_log):
    win = tk.Toplevel(root)
    win.title("Protocol Animation | " + protocol)
    win.geometry("1120x760")
    win.minsize(850, 640)
    win.configure(bg=BG)

    style = ttk.Style(win)
    style.configure(
        "Anim.TButton",
        background="#1c2c43",
        foreground=TEXT,
        padding=(12, 7),
        font=("Segoe UI", 9, "bold")
    )
    style.map(
        "Anim.TButton",
        background=[("active", "#2b4262")]
    )

    # ---------------- HEADER ----------------

    head = tk.Frame(win, bg=BG)
    head.pack(fill="x", padx=18, pady=(14, 8))

    tk.Label(
        head,
        text="LIVE PACKET FLOW",
        bg=BG,
        fg=BLUE,
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w")

    tk.Label(
        head,
        text=f"{protocol}  |  Sender ↔ Receiver",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 20, "bold")
    ).pack(anchor="w")

    tk.Label(
        head,
        text="Watch data frames, acknowledgements, losses and retransmissions.",
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(3, 0))

    # ---------------- NETWORK CANVAS ----------------

    canvas_box = tk.Frame(
        win,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    canvas_box.pack(
        fill="x",
        padx=18,
        pady=(0, 10)
    )

    canvas = tk.Canvas(
        canvas_box,
        height=300,
        bg="#0e192a",
        highlightthickness=0
    )
    canvas.pack(fill="x", padx=8, pady=8)

    status = tk.Label(
        win,
        text="Ready to play simulation events",
        bg=PANEL,
        fg=TEXT,
        anchor="w",
        padx=12,
        pady=10,
        font=("Segoe UI", 10, "bold")
    )
    status.pack(fill="x", padx=18, pady=(0, 10))

    # ---------------- EVENT LOG ----------------

    log_box = tk.Frame(
        win,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    log_box.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(0, 10)
    )

    log_head = tk.Frame(log_box, bg=PANEL)
    log_head.pack(fill="x", padx=10, pady=(8, 4))

    tk.Label(
        log_head,
        text="EVENT TIMELINE",
        bg=PANEL,
        fg=TEXT,
        font=("Segoe UI", 10, "bold")
    ).pack(side="left")

    counter = tk.Label(
        log_head,
        text=f"0 / {len(event_log)} events",
        bg=PANEL,
        fg=MUTED,
        font=("Segoe UI", 9)
    )
    counter.pack(side="right")

    txt_frame = tk.Frame(log_box, bg=PANEL)
    txt_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(0, 10)
    )

    log = tk.Text(
        txt_frame,
        height=8,
        wrap="word",
        state="disabled",
        bg="#08111f",
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        padx=10,
        pady=8,
        font=("Consolas", 10)
    )

    scroll = ttk.Scrollbar(
        txt_frame,
        orient="vertical",
        command=log.yview
    )
    log.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    log.pack(side="left", fill="both", expand=True)

    for tag, color in [
        ("send", "#93c5fd"),
        ("receive", "#86efac"),
        ("ack", "#4ade80"),
        ("lost", "#fca5a5"),
        ("ack_lost", "#fca5a5"),
        ("timeout", "#fdba74"),
        ("retransmit", "#fbbf24"),
        ("complete", "#c4b5fd"),
        ("muted", MUTED)
    ]:
        log.tag_configure(tag, foreground=color)

    # ---------------- PLAYBACK STATE ----------------

    state = {
        "index": 0,
        "paused": True,
        "after": None,
        "animation_ids": set(),
        "closed": False
    }

    # ---------------- DRAW NETWORK ----------------

    def draw_network():
        canvas.delete("network")

        width = max(canvas.winfo_width(), 820)
        height = max(canvas.winfo_height(), 300)

        left1 = 30
        right1 = 185
        right2 = width - 30
        left2 = width - 185

        cy = height // 2
        data_y = cy - 25
        ack_y = cy + 30

        canvas.create_text(
            width // 2,
            22,
            text=f"Protocol: {protocol}    •    Frames configured: {num_frames}",
            fill=MUTED,
            font=("Segoe UI", 10),
            tags="network"
        )

        # Sender
        canvas.create_rectangle(
            left1, cy - 55,
            right1, cy + 55,
            fill="#172e4d",
            outline=BLUE,
            width=2,
            tags="network"
        )

        canvas.create_text(
            (left1 + right1) // 2,
            cy - 8,
            text="SENDER",
            fill="#dbeafe",
            font=("Segoe UI", 13, "bold"),
            tags="network"
        )

        canvas.create_text(
            (left1 + right1) // 2,
            cy + 19,
            text="Transmit queue",
            fill="#93c5fd",
            font=("Segoe UI", 9),
            tags="network"
        )

        # Receiver
        canvas.create_rectangle(
            left2, cy - 55,
            right2, cy + 55,
            fill="#143526",
            outline=GREEN,
            width=2,
            tags="network"
        )

        canvas.create_text(
            (left2 + right2) // 2,
            cy - 8,
            text="RECEIVER",
            fill="#dcfce7",
            font=("Segoe UI", 13, "bold"),
            tags="network"
        )

        canvas.create_text(
            (left2 + right2) // 2,
            cy + 19,
            text="Receive buffer",
            fill="#86efac",
            font=("Segoe UI", 9),
            tags="network"
        )

        # Data path
        canvas.create_line(
            right1, data_y,
            left2, data_y,
            fill=BLUE,
            width=2,
            arrow=tk.LAST,
            tags="network"
        )

        # ACK path
        canvas.create_line(
            left2, ack_y,
            right1, ack_y,
            fill=GREEN,
            width=2,
            arrow=tk.LAST,
            tags="network"
        )

        canvas.create_text(
            (right1 + left2) // 2,
            data_y - 17,
            text="DATA FRAMES  →",
            fill="#93c5fd",
            font=("Segoe UI", 10, "bold"),
            tags="network"
        )

        canvas.create_text(
            (right1 + left2) // 2,
            ack_y + 17,
            text="←  ACKNOWLEDGEMENTS",
            fill="#86efac",
            font=("Segoe UI", 10, "bold"),
            tags="network"
        )

        return {
            "start_data": right1 + 12,
            "end_data": left2 - 12,
            "start_ack": left2 - 12,
            "end_ack": right1 + 12,
            "data_y": data_y,
            "ack_y": ack_y,
            "center": width // 2,
            "bottom": height - 20
        }

    win.update_idletasks()
    draw_network()

    # ---------------- SCHEDULE ANIMATION ----------------

    def later(callback, milliseconds):
        if state["closed"]:
            return

        holder = {"id": None}

        def run():
            state["animation_ids"].discard(holder["id"])

            if not state["closed"] and win.winfo_exists():
                callback()

        holder["id"] = win.after(milliseconds, run)
        state["animation_ids"].add(holder["id"])

    # ---------------- SHOW STATUS MARKER ----------------

    def marker(text, color):
        positions = draw_network()

        item = canvas.create_text(
            positions["center"],
            positions["bottom"],
            text=text,
            fill=color,
            font=("Segoe UI", 11, "bold")
        )

        later(lambda: canvas.delete(item), 1100)

    # ---------------- ANIMATE DATA OR ACK ----------------

    def token(event, direction):
        positions = draw_network()

        frame = event.get("frame", "?")
        seq = frame % 2 if isinstance(frame, int) else "?"
        is_data = direction == "data"

        if is_data:
            start = positions["start_data"]
            end = positions["end_data"]
            y = positions["data_y"]
        else:
            start = positions["start_ack"]
            end = positions["end_ack"]
            y = positions["ack_y"]

        event_type = event.get("type", "")

        if is_data:
            color = ORANGE if event_type == "retransmit" else BLUE

            if protocol == "One-Bit Sliding Window":
                label = f"F{frame} / S{seq}"
            else:
                label = f"F{frame}"
        else:
            color = GREEN

            if protocol == "One-Bit Sliding Window":
                label = f"ACK {seq}"
            else:
                label = f"ACK {frame}"

        ball = canvas.create_oval(
            start - 24, y - 13,
            start + 24, y + 13,
            fill=color,
            outline="white"
        )

        text = canvas.create_text(
            start,
            y,
            text=label,
            fill="white",
            font=("Segoe UI", 8, "bold")
        )

        steps = 32
        dx = (end - start) / steps
        step = {"n": 0}

        def move():
            if state["closed"] or not win.winfo_exists():
                return

            if step["n"] >= steps:
                canvas.delete(ball)
                canvas.delete(text)
                return

            canvas.move(ball, dx, 0)
            canvas.move(text, dx, 0)

            step["n"] += 1
            later(move, 18)

        move()

    # ---------------- PROCESS EVENT ----------------

    def render_event(event, index):
        event_type = event.get("type", "")
        frame = event.get("frame", "?")
        message = event.get("message", event_type)

        status.config(
            text=f"Event {index + 1}/{len(event_log)}  •  {message}"
        )

        counter.config(
            text=f"{index + 1} / {len(event_log)} events"
        )

        log.configure(state="normal")

        log.insert(
            "end",
            f'{index + 1:03d}  {event.get("time", 0):>7} ms   ',
            "muted"
        )

        tag = event_type if event_type in (
            "send",
            "receive",
            "ack",
            "lost",
            "ack_lost",
            "timeout",
            "retransmit",
            "complete"
        ) else "normal"

        log.insert("end", message + "\n", tag)
        log.see("end")
        log.configure(state="disabled")

        if event_type in ("send", "retransmit"):
            token(event, "data")

        elif event_type == "ack":
            token(event, "ack")

        elif event_type == "receive":
            marker(
                f"✓ Frame {frame} received",
                GREEN
            )

        elif event_type == "lost":
            marker(
                f"✕ FRAME {frame} LOST",
                RED
            )

        elif event_type == "ack_lost":
            marker(
                f"✕ ACK {frame} LOST",
                RED
            )

        elif event_type == "timeout":
            marker(
                f"TIMEOUT • Frame {frame}",
                ORANGE
            )

        elif event_type == "complete":
            marker(
                "SIMULATION COMPLETE",
                "#c4b5fd"
            )

    # ---------------- PLAYBACK CONTROLS ----------------

    def finish():
        state["after"] = None
        state["paused"] = True

        status.config(text="Playback completed")
        play_button.config(state="normal")
        pause_button.config(state="disabled")
        step_button.config(state="disabled")

    def play_next():
        state["after"] = None

        if state["closed"] or state["paused"]:
            return

        if state["index"] >= len(event_log):
            finish()
            return

        index = state["index"]
        state["index"] += 1

        render_event(event_log[index], index)

        state["after"] = win.after(520, play_next)

    def play():
        if not event_log:
            messagebox.showwarning(
                "No Events",
                "No simulation events are available.",
                parent=win
            )
            return

        if state["index"] >= len(event_log):
            restart()

        state["paused"] = False

        play_button.config(state="disabled")
        pause_button.config(state="normal")
        step_button.config(state="disabled")

        play_next()

    def pause_playback():
        state["paused"] = True

        if state["after"] is not None:
            try:
                win.after_cancel(state["after"])
            except tk.TclError:
                pass

            state["after"] = None

        play_button.config(state="normal")
        pause_button.config(state="disabled")
        step_button.config(state="normal")

        status.config(text="Playback paused")

    def step():
        if state["index"] >= len(event_log):
            finish()
            return

        index = state["index"]
        state["index"] += 1

        render_event(event_log[index], index)

        if state["index"] >= len(event_log):
            status.config(text="Playback completed")

    def restart():
        if state["after"] is not None:
            try:
                win.after_cancel(state["after"])
            except tk.TclError:
                pass

            state["after"] = None

        for after_id in list(state["animation_ids"]):
            try:
                win.after_cancel(after_id)
            except tk.TclError:
                pass

        state["animation_ids"].clear()
        state["index"] = 0
        state["paused"] = True

        log.configure(state="normal")
        log.delete("1.0", "end")
        log.configure(state="disabled")

        counter.config(
            text=f"0 / {len(event_log)} events"
        )

        status.config(text="Ready to play simulation events")

        draw_network()

        play_button.config(state="normal")
        pause_button.config(state="disabled")
        step_button.config(state="normal")

    # ---------------- BUTTONS ----------------

    controls = tk.Frame(win, bg=BG)
    controls.pack(
        fill="x",
        padx=18,
        pady=(0, 12)
    )

    play_button = ttk.Button(
        controls,
        text="▶  PLAY",
        style="Anim.TButton",
        command=play
    )
    play_button.pack(side="left", padx=(0, 7))

    pause_button = ttk.Button(
        controls,
        text="Ⅱ  PAUSE",
        style="Anim.TButton",
        command=pause_playback,
        state="disabled"
    )
    pause_button.pack(side="left", padx=7)

    step_button = ttk.Button(
        controls,
        text="→  NEXT EVENT",
        style="Anim.TButton",
        command=step
    )
    step_button.pack(side="left", padx=7)

    ttk.Button(
        controls,
        text="↻  RESTART",
        style="Anim.TButton",
        command=restart
    ).pack(side="left", padx=7)

    tk.Label(
        controls,
        text=f"{num_frames} frames configured",
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(side="right")

    # ---------------- CLOSE WINDOW SAFELY ----------------

    def close():
        state["closed"] = True

        if state["after"] is not None:
            try:
                win.after_cancel(state["after"])
            except tk.TclError:
                pass

        for after_id in list(state["animation_ids"]):
            try:
                win.after_cancel(after_id)
            except tk.TclError:
                pass

        win.destroy()

    win.protocol("WM_DELETE_WINDOW", close)

    return win


# ---------------- STANDALONE TEST ----------------

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    demo_events = [
        {
            "type": "send",
            "frame": 0,
            "message": "Frame 0 sent",
            "time": 0
        },
        {
            "type": "receive",
            "frame": 0,
            "message": "Receiver accepted Frame 0",
            "time": 100
        },
        {
            "type": "ack",
            "frame": 0,
            "message": "ACK 0 received",
            "time": 150
        },
        {
            "type": "lost",
            "frame": 1,
            "message": "Frame 1 lost",
            "time": 200
        },
        {
            "type": "timeout",
            "frame": 1,
            "message": "Timeout for Frame 1",
            "time": 500
        },
        {
            "type": "retransmit",
            "frame": 1,
            "message": "Frame 1 retransmitted",
            "time": 500
        },
        {
            "type": "complete",
            "frame": None,
            "message": "Simulation completed",
            "time": 650
        }
    ]

    show_animation(
        root,
        "Go-Back-N",
        2,
        demo_events
    )

    root.mainloop()
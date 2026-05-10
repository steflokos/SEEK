import tkinter as tk
from tkinter import ttk, filedialog
import threading
import queue
import os

from hardware import SerialManager
from campaign import CampaignEngine
from mapper import extract_targets


class SEMHybridEngineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("S.E.E.K. - Soft Error Exploration Kit")
        self.root.geometry("1920x1080")
        self.root.minsize(1920, 1080)

        self.bg_main = "#1E2128"
        self.bg_card = "#282C34"
        self.bg_inset = "#323641"
        self.text_main = "#ABB2BF"
        self.text_heading = "#E5E9F0"
        self.text_muted = "#9CA3AF"
        self.border_color = "#3E4451"

        self.root.configure(bg=self.bg_main)

        # Cross-module communication setup
        self.log_queue = queue.Queue()
        self.serial_manager = SerialManager(log_callback=self.log)
        self.engine = CampaignEngine(
            self.serial_manager,
            self.log,
            self._update_progress,
            self._on_campaign_complete,
        )

        self._setup_styles()
        self._build_ui()
        self.root.after(100, self._process_log_queue)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        primary = "#4D78CC"  
        primary_hover = "#618DE0"
        success = "#5C9E5C"  
        success_hover = "#6FB26F"
        danger = "#CC5B60" 
        danger_hover = "#E06D72"
        warning = "#D19A66"
        warning_hover = "#E5A869"
        tertiary = "#4C99A0"  
        tertiary_hover = "#5EADB4"
        btn_bg = "#3A3F4B"
        btn_hover = "#4C525D"

        style.configure(
            ".",
            background=self.bg_main,
            foreground=self.text_main,
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=self.bg_main)
        style.configure("Card.TFrame", background=self.bg_card)
        style.configure(
            "Card.TLabelframe",
            background=self.bg_card,
            bordercolor=self.border_color,
            borderwidth=1,
            relief="flat",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.bg_card,
            foreground=self.text_heading,
            font=("Segoe UI", 10, "bold"),
            padding=(0, 8),
        )

        style.configure(
            "Card.TLabel", background=self.bg_card, foreground=self.text_main
        )
        style.configure(
            "Card.TCheckbutton", background=self.bg_card, foreground=self.text_main
        )
        style.map(
            "Card.TCheckbutton",
            background=[("active", self.bg_card), ("pressed", self.bg_card)],
            foreground=[("active", self.text_heading)],
        )

        style.configure(
            "TButton",
            padding=6,
            relief="flat",
            background=btn_bg,
            foreground=self.text_heading,
            font=("Segoe UI", 10),
        )
        style.map(
            "TButton",
            background=[("active", btn_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "Primary.TButton",
            background=primary,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", primary_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "Connect.TButton",
            background=success,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Connect.TButton",
            background=[("active", success_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "Disconnect.TButton",
            background=danger,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Disconnect.TButton", background=[("active", danger_hover)])

        style.configure(
            "Abort.TButton",
            background=danger,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Abort.TButton",
            background=[("active", danger_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "Tertiary.TButton",
            background=tertiary,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Tertiary.TButton",
            background=[("active", tertiary_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "Warning.TButton",
            background=warning,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Warning.TButton",
            background=[("active", warning_hover)],
            foreground=[("disabled", self.text_muted)],
        )
        style.map(
            "Tertiary.TButton",
            background=[("active", tertiary_hover)],
            foreground=[("disabled", self.text_muted)],
        )

        style.configure(
            "TEntry",
            padding=5,
            relief="flat",
            fieldbackground=self.bg_inset,
            foreground=self.text_heading,
            borderwidth=1,
            bordercolor=self.border_color,
        )
        style.map("TEntry", fieldbackground=[("readonly", self.bg_card)])

        style.configure(
            "TCombobox",
            padding=5,
            relief="flat",
            fieldbackground=self.bg_inset,
            foreground=self.text_heading,
            borderwidth=1,
            bordercolor=self.border_color,
        )
        style.map("TCombobox", fieldbackground=[("readonly", self.bg_inset)])

        style.configure(
            "TSpinbox",
            padding=5,
            relief="flat",
            fieldbackground=self.bg_inset,
            foreground=self.text_heading,
            borderwidth=1,
            bordercolor=self.border_color,
        )

        style.configure("TPanedwindow", background=self.bg_main)
        style.configure("Sash", background=self.border_color, sashthickness=2)
        style.configure(
            "Vertical.TScrollbar",
            background=self.bg_card,
            troughcolor=self.bg_main,
            arrowcolor=self.text_muted,
            bordercolor=self.bg_card,
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=self.bg_card,
            troughcolor=self.bg_main,
            arrowcolor=self.text_muted,
            bordercolor=self.bg_card,
        )

        style.configure(
            "TProgressbar",
            troughcolor=self.bg_inset,
            background=primary,
            bordercolor=self.bg_card,
            thickness=8,
        )

    def _build_ui(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # ==========================================
        # LEFT PANE: CONTROLS
        # ==========================================
        left_frame = ttk.Frame(main_pane, width=480)
        main_pane.add(left_frame, weight=0)

        # --- Target Manager (Hybrid) ---
        map_frame = ttk.LabelFrame(
            left_frame, text="1. Target Manager (Map or Load)", padding=15
        )
        map_frame.pack(fill=tk.X, pady=(0, 15))
        self._set_card_bg(map_frame)

        self.ll_var, self.ebd_var = tk.StringVar(), tk.StringVar()

        ttk.Label(map_frame, text="LL File:", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", pady=4
        )
        ttk.Entry(map_frame, textvariable=self.ll_var).grid(
            row=0, column=1, sticky="ew", padx=5, pady=4
        )
        ttk.Button(
            map_frame, text="Browse", width=8, command=lambda: self._browse("ll")
        ).grid(row=0, column=2, pady=4)

        ttk.Label(map_frame, text="EBD File:", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Entry(map_frame, textvariable=self.ebd_var).grid(
            row=1, column=1, sticky="ew", padx=5, pady=4
        )
        ttk.Button(
            map_frame, text="Browse", width=8, command=lambda: self._browse("ebd")
        ).grid(row=1, column=2, pady=4)

        map_frame.columnconfigure(1, weight=1)

        param_f1 = ttk.Frame(map_frame, style="Card.TFrame")
        param_f1.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 5))

        # IP Field
        ttk.Label(param_f1, text="IP:", style="Card.TLabel").pack(side=tk.LEFT)
        self.target_ip_var = tk.StringVar(value="design_1_i/c_addsub_0")
        ttk.Entry(param_f1, textvariable=self.target_ip_var, width=15).pack(
            side=tk.LEFT, padx=(5, 10)
        )

        # Architecture Field
        ttk.Label(param_f1, text="Arch:", style="Card.TLabel").pack(side=tk.LEFT)
        self.arch_var = tk.StringVar(value="7-Series (Artix/Kintex)")
        ttk.Combobox(
            param_f1,
            textvariable=self.arch_var,
            values=["7-Series (Artix/Kintex)", "UltraScale", "UltraScale+"],
            width=20,
            state="readonly",
        ).pack(side=tk.LEFT, padx=(5, 10))

        # Words Field
        ttk.Label(param_f1, text="Words:", style="Card.TLabel").pack(side=tk.LEFT)
        self.words_var = tk.StringVar(value="101")
        ttk.Combobox(
            param_f1, textvariable=self.words_var, values=["93", "101", "123"], width=4
        ).pack(side=tk.LEFT, padx=5)

        # Bind the trace so words change automatically when architecture changes
        self.arch_var.trace_add("write", self._on_arch_changed)

        self.btn_map = ttk.Button(
            map_frame,
            text="Extract Bits to Editor",
            style="Primary.TButton",
            command=self._run_mapping_thread,
        )
        self.btn_map.grid(row=3, column=0, columnspan=3, pady=(15, 10), sticky="ew")

        ttk.Separator(map_frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=10
        )

        btn_frame_1 = ttk.Frame(map_frame, style="Card.TFrame")
        btn_frame_1.grid(row=5, column=0, columnspan=3, sticky="ew")
        ttk.Button(
            btn_frame_1, text="Load Targets (.txt)", command=self._load_targets
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btn_frame_1, text="Clear Editor", command=self._clear_editor).pack(
            side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0)
        )

        # --- Hardware Connection ---
        uart_frame = ttk.LabelFrame(
            left_frame, text="2. Hardware Connection", padding=15
        )
        uart_frame.pack(fill=tk.X, pady=(0, 15))
        self._set_card_bg(uart_frame)

        uart_top = ttk.Frame(uart_frame, style="Card.TFrame")
        uart_top.pack(fill=tk.X)
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(uart_top, textvariable=self.port_var, width=15)
        self.port_cb.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(uart_top, text="Refresh", width=8, command=self._refresh_ports).pack(
            side=tk.LEFT
        )
        self._refresh_ports()

        self.nl_var = tk.StringVar(value="CRLF")
        ttk.Combobox(
            uart_top,
            textvariable=self.nl_var,
            values=["CRLF", "CR", "LF", "None"],
            width=5,
            state="readonly",
        ).pack(side=tk.RIGHT)

        self.baud_var = tk.StringVar(value="115200")
        ttk.Combobox(
            uart_top, textvariable=self.baud_var, values=["9600", "115200"], width=8
        ).pack(side=tk.RIGHT, padx=(5, 5))

        self.btn_connect = ttk.Button(
            uart_frame,
            text="Connect UART",
            style="Connect.TButton",
            command=self._toggle_connection,
        )
        self.btn_connect.pack(fill=tk.X, pady=(15, 0))

        # --- Execution Engine ---
        camp_frame = ttk.LabelFrame(left_frame, text="3. Execution Engine", padding=15)
        camp_frame.pack(fill=tk.X, pady=(0, 5))
        self._set_card_bg(camp_frame)

        param_f2 = ttk.Frame(camp_frame, style="Card.TFrame")
        param_f2.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(param_f2, text="Injection Delay (sec):", style="Card.TLabel").pack(
            side=tk.LEFT
        )
        self.delay_var = tk.DoubleVar(value=1.5)
        ttk.Spinbox(
            param_f2,
            from_=0.1,
            to=5.0,
            increment=0.1,
            textvariable=self.delay_var,
            width=6,
        ).pack(side=tk.LEFT, padx=10)

        self.send_o_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            camp_frame,
            text="Auto-Scrub (Send 'O' after delay)",
            variable=self.send_o_var,
            style="Card.TCheckbutton",
        ).pack(anchor="w", pady=(0, 15))

        batch_f = ttk.Frame(camp_frame, style="Card.TFrame")
        batch_f.pack(fill=tk.X, pady=(0, 10))
        self.btn_run = ttk.Button(
            batch_f,
            text="Run Target List",
            style="Connect.TButton",
            state=tk.DISABLED,
            command=self._start_batch,
        )
        self.btn_run.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.btn_abort = ttk.Button(
            batch_f,
            text="Abort Campaign",
            style="Abort.TButton",
            state=tk.DISABLED,
            command=self._abort_campaign,
        )
        self.btn_abort.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        self.progress = ttk.Progressbar(camp_frame, mode="determinate")
        self.progress.pack(fill=tk.X, pady=5)

        ttk.Separator(camp_frame, orient="horizontal").pack(fill=tk.X, pady=15)

        # Discovery Engine Controls
        disc_top = ttk.Frame(camp_frame, style="Card.TFrame")
        disc_top.pack(fill=tk.X, pady=(0, 10))

        self.btn_disc = ttk.Button(
            disc_top,
            text="Start Discovery (Auto Scrubbing)",
            style="Tertiary.TButton",
            state=tk.DISABLED,
            command=self._start_discovery,
        )
        self.btn_disc.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # NEW: Stop Discovery Button
        self.btn_disc_stop = ttk.Button(
            disc_top,
            text="Stop Discovery",
            style="Abort.TButton",
            state=tk.DISABLED,
            command=self._stop_discovery,
        )
        self.btn_disc_stop.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        disc_ctrl = ttk.Frame(camp_frame, style="Card.TFrame")
        disc_ctrl.pack(fill=tk.X)
        self.btn_save = ttk.Button(
            disc_ctrl,
            text="Mark Broken (Save)",
            style="Warning.TButton",
            state=tk.DISABLED,
            command=self._disc_save,
        )
        self.btn_save.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.btn_skip = ttk.Button(
            disc_ctrl, text="Skip Fault", state=tk.DISABLED, command=self._disc_skip
        )
        self.btn_skip.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        # ==========================================
        # RIGHT PANE: EDITORS & TERMINAL
        # ==========================================
        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=1)

        editor_frame = ttk.LabelFrame(
            right_pane, text="Target Editor (List to Execute)", padding=10
        )
        right_pane.add(editor_frame, weight=1)
        self._set_card_bg(editor_frame)

        ed_border = tk.Frame(editor_frame, bg=self.border_color, bd=1)
        ed_border.pack(fill=tk.BOTH, expand=True)

        self.line_numbers = tk.Text(
            ed_border,
            width=4,
            padx=5,
            pady=5,
            border=0,
            background=self.bg_card,
            state="disabled",
            font=("Consolas", 11),
            fg=self.text_muted,
            insertbackground=self.text_main,
            takefocus=0,
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.target_text = tk.Text(
            ed_border,
            font=("Consolas", 11),
            bg=self.bg_main,
            fg="#D4D4D4",
            insertbackground=self.text_heading,
            selectbackground="#264F78",
            selectforeground="#FFFFFF",
            border=0,
            undo=True,
            padx=10,
            pady=5,
            wrap="none",
            relief="flat",
        )
        self.target_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_ed = ttk.Scrollbar(editor_frame, command=self._sync_yview)
        self.scroll_ed.pack(side=tk.RIGHT, fill=tk.Y)
        self.target_text.configure(
            yscrollcommand=self._sync_scroll_set, highlightthickness=0
        )

        self.target_text.bind("<KeyRelease>", self._update_line_numbers)
        self.target_text.bind("<MouseWheel>", self._update_line_numbers)
        self.target_text.bind("<ButtonRelease-1>", self._update_line_numbers)
        self.target_text.bind("<<Modified>>", self._update_line_numbers)

        term_frame = ttk.LabelFrame(right_pane, text="Live SEM Terminal", padding=10)
        right_pane.add(term_frame, weight=1)
        self._set_card_bg(term_frame)

        tx_frame = ttk.Frame(term_frame, style="Card.TFrame")
        tx_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        ttk.Label(tx_frame, text="Command >", style="Card.TLabel").pack(
            side=tk.LEFT, padx=(0, 5)
        )

        self.cmd_entry = ttk.Entry(tx_frame, font=("Consolas", 11))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self._send_manual())

        ttk.Button(
            tx_frame,
            text="Send TX",
            style="Primary.TButton",
            command=self._send_manual,
            width=10,
        ).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(tx_frame, text="Clear", command=self._clear_terminal, width=8).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        term_border = tk.Frame(term_frame, bg=self.border_color, bd=1)
        term_border.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.terminal = tk.Text(
            term_border,
            state=tk.DISABLED,
            bg="#111111",
            fg="#D4D4D4",
            border=0,
            padx=10,
            pady=10,
            font=("Consolas", 10),
            insertbackground="#D4D4D4",
            selectbackground="#264F78",
            selectforeground="#FFFFFF",
            relief="flat",
        )

        scroll_term = ttk.Scrollbar(term_border, command=self.terminal.yview)
        self.terminal.configure(yscrollcommand=scroll_term.set, highlightthickness=0)

        self.terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_term.pack(side=tk.RIGHT, fill=tk.Y)

        self.cmd_entry.focus_set()
        self._update_line_numbers()

    # --- Events ---
    def _on_arch_changed(self, *args):
        arch = self.arch_var.get()
        if arch == "7-Series (Artix/Kintex)":
            self.words_var.set("101")
        elif arch == "UltraScale":
            self.words_var.set("123")
        elif arch == "UltraScale+":
            self.words_var.set("93")

    def _get_endline(self):
        val = self.nl_var.get()
        if val == "CRLF":
            return "\r\n"
        elif val == "CR":
            return "\r"
        elif val == "LF":
            return "\n"
        else:
            return ""

    # --- UI Helpers ---
    def _set_card_bg(self, parent):
        parent.configure(style="Card.TLabelframe")

    def _browse(self, ftype):
        path = filedialog.askopenfilename(filetypes=[("Files", f"*.{ftype}")])
        if path:
            (self.ll_var if ftype == "ll" else self.ebd_var).set(path)

    def _sync_yview(self, *args):
        self.target_text.yview(*args)
        self.line_numbers.yview(*args)

    def _sync_scroll_set(self, *args):
        self.scroll_ed.set(*args)
        self.line_numbers.yview_moveto(args[0])
        self._update_line_numbers()

    def _update_line_numbers(self, event=None):
        line_count = int(self.target_text.index("end-1c").split(".")[0])
        line_num_string = "\n".join(str(i) for i in range(1, line_count + 1))

        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_num_string)
        self.line_numbers.config(state=tk.DISABLED)
        self.line_numbers.yview_moveto(self.target_text.yview()[0])
        self.target_text.edit_modified(False)

    def _get_targets_from_editor(self):
        raw_text = self.target_text.get("1.0", tk.END).splitlines()
        return [
            line.strip()
            for line in raw_text
            if line.strip() and not line.strip().startswith("#")
        ]

    def _clear_editor(self):
        self.target_text.delete("1.0", tk.END)
        self._update_line_numbers()

    def _clear_terminal(self):
        """Wipes the Live SEM Terminal display."""
        self.terminal.configure(state=tk.NORMAL)
        self.terminal.delete("1.0", tk.END)
        self.terminal.configure(state=tk.DISABLED)

    def _load_targets(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            try:
                with open(path, "r") as f:
                    content = f.read()
                self._clear_editor()
                self.target_text.insert(tk.END, content)
                self._update_line_numbers()
                self.log(
                    f"\n[System] Loaded {len(self._get_targets_from_editor())} targets from {os.path.basename(path)}"
                )
            except Exception as e:
                self.log(f"[Error] Failed to read file: {e}")

    # --- Connected Module Logic ---
    def log(self, msg):
        self.log_queue.put(msg)

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.terminal.configure(state=tk.NORMAL)
            self.terminal.insert(tk.END, msg + "\n")
            self.terminal.see(tk.END)
            self.terminal.configure(state=tk.DISABLED)
        self.root.after(100, self._process_log_queue)

    def _refresh_ports(self):
        ports = self.serial_manager.get_ports()
        self.port_cb["values"] = ports
        if ports:
            self.port_cb.current(0)

    def _toggle_connection(self):
        if self.serial_manager.is_connected:
            self.serial_manager.disconnect()
            self.btn_connect.config(text="Connect UART", style="Connect.TButton")
            self.btn_run.config(state=tk.DISABLED)
            self.btn_disc.config(state=tk.DISABLED)
            self.btn_disc_stop.config(state=tk.DISABLED)
            self.log("\n[System] Disconnected.")
        else:
            try:
                self.serial_manager.connect(self.port_var.get(), self.baud_var.get())
                self.btn_connect.config(
                    text="Disconnect UART", style="Disconnect.TButton"
                )
                self.btn_run.config(state=tk.NORMAL)
                self.btn_disc.config(state=tk.NORMAL)
                self.log(f"\n[System] Connected to {self.port_var.get()}.")
            except Exception as e:
                self.log(f"[Error] {e}")

    def _send_manual(self):
        cmd = self.cmd_entry.get().strip()
        if cmd and self.serial_manager.is_connected:
            self.log(f"\n[TX] {cmd}")
            self.serial_manager.write((cmd + self._get_endline()).encode("ascii"))
            self.cmd_entry.delete(0, tk.END)

    def _run_mapping_thread(self):
        threading.Thread(target=self._run_mapping, daemon=True).start()

    def _run_mapping(self):
        self.btn_map.config(state=tk.DISABLED)
        self.log(f"\n--- MAPPER: Extracting '{self.target_ip_var.get()}' ---")
        try:
            targets = extract_targets(
                self.ll_var.get(),
                self.ebd_var.get(),
                self.target_ip_var.get(),
                int(self.words_var.get()),
                self.arch_var.get(),
            )
            self.root.after(0, lambda: self._on_mapping_complete(targets))
        except Exception as e:
            self.log(f"[Error] Mapping Failed: {e}")
            self.root.after(0, lambda: self.btn_map.config(state=tk.NORMAL))

    def _on_mapping_complete(self, targets):
        self._clear_editor()
        self.target_text.insert(
            tk.END,
            f"# Extracted {len(targets)} targets for {self.target_ip_var.get()}\n",
        )
        self.target_text.insert(tk.END, "\n".join(targets))
        self._update_line_numbers()
        self.log(f"--- COMPLETE: Extracted {len(targets)} targets to the Editor. ---")
        self.btn_map.config(state=tk.NORMAL)

    def _start_batch(self):
        targets = self._get_targets_from_editor()
        if not targets:
            return self.log("[Error] Target Editor is empty.")

        self.btn_run.config(state=tk.DISABLED)
        self.btn_disc.config(state=tk.DISABLED)
        self.btn_abort.config(state=tk.NORMAL)
        self.progress["maximum"] = len(targets)
        self.progress["value"] = 0

        # Passes selected endline to the engine
        self.engine.start_batch(
            targets, self.delay_var.get(), self.send_o_var.get(), self._get_endline()
        )

    def _abort_campaign(self):
        self.engine.abort()

    def _start_discovery(self):
        targets = self._get_targets_from_editor()
        if not targets:
            return self.log("[Error] Target Editor is empty.")

        self.btn_run.config(state=tk.DISABLED)
        self.btn_disc.config(state=tk.DISABLED)
        self.btn_disc_stop.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.NORMAL)
        self.btn_skip.config(state=tk.NORMAL)

        # Passes selected endline to the engine
        self.engine.start_discovery(targets, self.delay_var.get(), self._get_endline())

    def _stop_discovery(self):
        self.engine.stop_discovery()

    def _update_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _on_campaign_complete(self):
        def reset_ui():
            self.btn_run.config(state=tk.NORMAL)
            self.btn_disc.config(state=tk.NORMAL)
            self.btn_abort.config(state=tk.DISABLED)
            self.btn_disc_stop.config(state=tk.DISABLED)
            self.btn_save.config(state=tk.DISABLED)
            self.btn_skip.config(state=tk.DISABLED)

        self.root.after(0, reset_ui)

    def _disc_save(self):
        self.engine.save_and_next()

    def _disc_skip(self):
        self.engine.skip_and_next()

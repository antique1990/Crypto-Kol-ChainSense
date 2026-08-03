#!/usr/bin/env python3
"""Standalone desktop interface for the Crypto Consensus report."""
import contextlib
import json
import os
import queue
import runpy
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText


def resource_root():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE = resource_root()
QF = os.path.join(BASE, 'quant_factors')
RUN_SCRIPT = os.path.join(QF, 'run_consensus.py')
DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser('~'), 'Desktop')
SYMBOLS = [('BTC', 'BTCUSDT'), ('ETH', 'ETHUSDT'), ('SOL', 'SOLUSDT'), ('DOGE', 'DOGEUSDT')]


class ConsensusGUI(tk.Tk):
    BG = '#0b1020'
    PANEL = '#131b31'
    PANEL_ALT = '#0f172a'
    TEXT = '#f8fafc'
    MUTED = '#94a3b8'
    ACCENT = '#38bdf8'
    POSITIVE = '#34d399'
    NEGATIVE = '#fb7185'

    def __init__(self):
        super().__init__()
        self.title('Crypto Consensus Terminal')
        self.geometry('1120x760')
        self.minsize(960, 660)
        self.configure(bg=self.BG)

        self.output_queue = queue.Queue()
        self.worker_thread = None
        self.current_symbol = None
        self.last_report_path = None
        self.output_dir = DEFAULT_OUTPUT_DIR if os.path.isdir(DEFAULT_OUTPUT_DIR) else os.path.expanduser('~')
        self.symbol_buttons = []
        self._configure_style()
        self._build_ui()
        self.after(100, self._process_queue)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('App.TFrame', background=self.BG)
        style.configure('Card.TFrame', background=self.PANEL)
        style.configure('Title.TLabel', background=self.BG, foreground=self.TEXT, font=('Segoe UI', 23, 'bold'))
        style.configure('Sub.TLabel', background=self.BG, foreground=self.MUTED, font=('Segoe UI', 10))
        style.configure('CardTitle.TLabel', background=self.PANEL, foreground=self.TEXT, font=('Segoe UI', 11, 'bold'))
        style.configure('CardText.TLabel', background=self.PANEL, foreground=self.MUTED, font=('Segoe UI', 10))
        style.configure('Value.TLabel', background=self.PANEL, foreground=self.TEXT, font=('Segoe UI', 10, 'bold'))
        style.configure('Asset.TButton', font=('Segoe UI', 11, 'bold'), padding=(14, 10), foreground=self.TEXT, background='#1e3a5f', borderwidth=0)
        style.map('Asset.TButton', background=[('active', '#075985'), ('disabled', '#26344b')], foreground=[('disabled', '#64748b')])
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), padding=(12, 8), foreground='#082f49', background=self.ACCENT, borderwidth=0)
        style.map('Primary.TButton', background=[('active', '#7dd3fc'), ('disabled', '#334155')], foreground=[('disabled', '#94a3b8')])
        style.configure('Quiet.TButton', font=('Segoe UI', 10), padding=(10, 7), foreground='#cbd5e1', background='#243049', borderwidth=0)
        style.map('Quiet.TButton', background=[('active', '#334155'), ('disabled', '#1e293b')])

    def _build_ui(self):
        root = ttk.Frame(self, style='App.TFrame', padding=24)
        root.grid(sticky='nsew')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)

        header = ttk.Frame(root, style='App.TFrame')
        header.grid(row=0, column=0, sticky='ew')
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text='CRYPTO CONSENSUS', style='Title.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(header, text='Quantitative trader intelligence  •  On-demand market briefings', style='Sub.TLabel').grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.status_badge = tk.Label(header, text='  READY  ', bg='#17324a', fg='#7dd3fc', font=('Segoe UI', 9, 'bold'), padx=8, pady=5)
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky='e')

        ttk.Label(root, text='SELECT ASSET', style='Sub.TLabel').grid(row=1, column=0, sticky='w', pady=(24, 8))
        asset_bar = ttk.Frame(root, style='App.TFrame')
        asset_bar.grid(row=2, column=0, sticky='ew')
        for i, (label, symbol) in enumerate(SYMBOLS):
            asset_bar.columnconfigure(i, weight=1)
            button = ttk.Button(asset_bar, text=f'{label} / USDT', style='Asset.TButton', command=lambda s=symbol: self.start_run(s))
            button.grid(row=0, column=i, sticky='ew', padx=(0 if i == 0 else 8, 0))
            self.symbol_buttons.append(button)

        info = ttk.Frame(root, style='Card.TFrame', padding=16)
        info.grid(row=3, column=0, sticky='ew', pady=(18, 0))
        info.columnconfigure(1, weight=1)
        ttk.Label(info, text='REPORT OUTPUT', style='CardTitle.TLabel').grid(row=0, column=0, sticky='w')
        self.output_label = ttk.Label(info, text=self.output_dir, style='CardText.TLabel')
        self.output_label.grid(row=0, column=1, sticky='w', padx=14)
        ttk.Button(info, text='Change folder', style='Quiet.TButton', command=self.choose_output_dir).grid(row=0, column=2, sticky='e')
        ttk.Label(info, text='STATUS', style='CardText.TLabel').grid(row=1, column=0, sticky='w', pady=(13, 0))
        self.status_label = ttk.Label(info, text='Choose an asset to generate the latest consensus report.', style='Value.TLabel')
        self.status_label.grid(row=1, column=1, columnspan=2, sticky='w', padx=14, pady=(13, 0))

        content = ttk.Frame(root, style='App.TFrame')
        content.grid(row=4, column=0, sticky='nsew', pady=(18, 0))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        log_card = ttk.Frame(content, style='Card.TFrame', padding=16)
        log_card.grid(row=0, column=0, sticky='nsew', padx=(0, 9))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        ttk.Label(log_card, text='ACTIVITY LOG', style='CardTitle.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.text_area = ScrolledText(log_card, wrap='word', font=('Cascadia Mono', 10), bg='#0a1224', fg='#cbd5e1', insertbackground='#ffffff', relief='flat', borderwidth=0, padx=12, pady=12)
        self.text_area.grid(row=1, column=0, sticky='nsew')
        self.text_area.configure(state='disabled')

        summary_card = ttk.Frame(content, style='Card.TFrame', padding=16)
        summary_card.grid(row=0, column=1, sticky='nsew', padx=(9, 0))
        summary_card.columnconfigure(0, weight=1)
        summary_card.rowconfigure(1, weight=1)
        ttk.Label(summary_card, text='LATEST CONSENSUS', style='CardTitle.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.summary_text = tk.Text(summary_card, wrap='word', font=('Segoe UI', 10), bg=self.PANEL, fg='#dbeafe', relief='flat', borderwidth=0, padx=4, pady=4, cursor='arrow')
        self.summary_text.grid(row=1, column=0, sticky='nsew')
        self._set_summary('Generate a report to see the current market bias, active factors, and leading trader signals.')

        footer = ttk.Frame(root, style='App.TFrame')
        footer.grid(row=5, column=0, sticky='ew', pady=(16, 0))
        footer.columnconfigure(2, weight=1)
        self.open_button = ttk.Button(footer, text='Open HTML report', style='Primary.TButton', command=self.open_report, state='disabled')
        self.open_button.grid(row=0, column=0, sticky='w')
        ttk.Button(footer, text='Clear log', style='Quiet.TButton', command=self.clear_output).grid(row=0, column=1, sticky='w', padx=8)
        self.progress = ttk.Progressbar(footer, mode='indeterminate')
        self.progress.grid(row=0, column=2, sticky='ew', padx=(12, 0))

    def _set_summary(self, text):
        self.summary_text.configure(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert(tk.END, text)
        self.summary_text.configure(state='disabled')

    def _set_status(self, text, state='ready'):
        colors = {'ready': ('#17324a', '#7dd3fc'), 'running': ('#3b2f12', '#fbbf24'), 'success': ('#12342c', '#6ee7b7'), 'error': ('#411b2a', '#fda4af')}
        bg, fg = colors[state]
        self.status_badge.configure(text=f'  {state.upper()}  ', bg=bg, fg=fg)
        self.status_label.configure(text=text)

    def choose_output_dir(self):
        selected = filedialog.askdirectory(initialdir=self.output_dir, title='Choose report output folder')
        if selected:
            self.output_dir = selected
            self.output_label.configure(text=selected)

    def clear_output(self):
        self.text_area.configure(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.configure(state='disabled')

    def append_line(self, line):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, line + '\n')
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')

    def _load_snapshot(self, symbol):
        filename = f'consensus_snapshot_{symbol}.json'
        for path in (os.path.join(self.output_dir, filename), os.path.join(QF, filename)):
            try:
                with open(path, encoding='utf-8') as handle:
                    return json.load(handle)
            except (OSError, ValueError):
                pass
        return None

    def _update_summary(self, symbol):
        snap = self._load_snapshot(symbol)
        if not snap:
            self._set_summary('The report was generated, but its snapshot file could not be read.')
            return
        consensus = snap.get('consensus', {})
        counts = consensus.get('equal_weight', {})
        bias = float(consensus.get('trust_adjusted', 0))
        direction = 'BULLISH' if bias > 0.01 else 'BEARISH' if bias < -0.01 else 'NEUTRAL'
        factors = snap.get('firing_factors', [])
        lines = [
            f'{symbol}  •  {snap.get("date", "Latest")}',
            f'Price  ${snap.get("price", 0):,.2f}',
            '', f'{direction}  {bias:+.3f}',
            'Trust-adjusted market bias', '',
            f"Trader consensus\nLong  {counts.get('long', 0)}    Short  {counts.get('short', 0)}    Neutral  {counts.get('neutral', 0)}",
            '', f'Active factors  {len(factors)}',
        ]
        for factor in factors[:6]:
            sign = '▲' if factor.get('score', 0) > 0 else '▼'
            lines.append(f"{sign}  {factor.get('id', '')}  {factor.get('score', 0):+.2f}")
        self._set_summary('\n'.join(lines))

    def _runner(self):
        if getattr(sys, 'frozen', False):
            script = os.path.join(getattr(sys, '_MEIPASS', BASE), 'quant_factors', 'run_consensus.py')
            return script if os.path.exists(script) else None
        return [sys.executable, RUN_SCRIPT] if os.path.exists(RUN_SCRIPT) else None

    def start_run(self, symbol):
        if self.worker_thread and self.worker_thread.is_alive():
            return
        runner = self._runner()
        if not runner:
            self.append_line('ERROR: bundled pipeline script was not found.')
            self._set_status('Bundled pipeline script was not found.', 'error')
            return
        self.current_symbol = symbol
        self.open_button.configure(state='disabled')
        self.clear_output()
        self.append_line(f'Preparing {symbol} consensus report…')
        self._set_status(f'Computing {symbol} factors and trader composites…', 'running')
        self.progress.start(14)
        for button in self.symbol_buttons:
            button.configure(state='disabled')
        if isinstance(runner, list):
            args = runner + [symbol, '--no-open', '--output-dir', self.output_dir]
            target, target_args = self._run_process, (args,)
        else:
            target, target_args = self._run_embedded, (runner, symbol)
        self.worker_thread = threading.Thread(target=target, args=target_args, daemon=True)
        self.worker_thread.start()

    def _run_process(self, args):
        try:
            process = subprocess.Popen(args, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            for line in process.stdout or []:
                self.output_queue.put(('line', line.rstrip()))
            process.wait()
            self.output_queue.put(('done', process.returncode))
        except Exception as exc:
            self.output_queue.put(('error', str(exc)))

    def _run_embedded(self, script, symbol):
        class QueueWriter:
            def __init__(self, output_queue): self.output_queue, self.buffer = output_queue, ''
            def write(self, text):
                self.buffer += text
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    self.output_queue.put(('line', line))
            def flush(self):
                if self.buffer: self.output_queue.put(('line', self.buffer)); self.buffer = ''
        writer, old_args, old_cwd = QueueWriter(self.output_queue), sys.argv, os.getcwd()
        try:
            sys.argv = [script, symbol, '--no-open', '--output-dir', self.output_dir]
            os.chdir(BASE)
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                runpy.run_path(script, run_name='__main__')
            self.output_queue.put(('done', 0))
        except SystemExit as exc:
            self.output_queue.put(('done', exc.code if isinstance(exc.code, int) else 0))
        except Exception as exc:
            self.output_queue.put(('error', str(exc)))
        finally:
            writer.flush(); sys.argv = old_args; os.chdir(old_cwd)

    def _process_queue(self):
        while True:
            try: kind, payload = self.output_queue.get_nowait()
            except queue.Empty: break
            if kind == 'line': self.append_line(payload)
            elif kind == 'error':
                self.append_line(f'ERROR: {payload}')
                self._set_status('Report generation failed. Review the activity log.', 'error')
                self.progress.stop()
                for button in self.symbol_buttons: button.configure(state='normal')
            elif kind == 'done':
                self.progress.stop()
                for button in self.symbol_buttons: button.configure(state='normal')
                if payload == 0 and self._find_report_path(self.current_symbol):
                    self.last_report_path = self._find_report_path(self.current_symbol)
                    self.open_button.configure(state='normal')
                    self._update_summary(self.current_symbol)
                    self._set_status(f'{self.current_symbol} report is ready.', 'success')
                    self.append_line('Report complete.')
                else:
                    self._set_status('Report generation did not complete.', 'error')
        self.after(100, self._process_queue)

    def _find_report_path(self, symbol):
        if not symbol: return None
        name = f'consensus_snapshot_{symbol}.html'
        for folder in (self.output_dir, QF):
            path = os.path.join(folder, name)
            if os.path.isfile(path): return path
        return None

    def open_report(self):
        path = self._find_report_path(self.current_symbol)
        if path: webbrowser.open('file:///' + os.path.abspath(path).replace('\\', '/'))


if __name__ == '__main__':
    ConsensusGUI().mainloop()

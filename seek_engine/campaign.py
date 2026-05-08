import threading
import time


class CampaignEngine:
    def __init__(
        self, serial_manager, log_callback, progress_callback, completion_callback
    ):
        self.serial = serial_manager
        self.log = log_callback
        self.update_progress = progress_callback
        self.on_complete = completion_callback

        self.active = False
        self.discovery_active = False
        self.discovery_targets = []
        self.discovery_idx = 0
        self.delay = 1.5
        self.endline = "\r\n"

    def start_batch(self, targets, delay, send_o, endline):
        self.active = True
        self.endline = endline
        threading.Thread(
            target=self._batch_thread, args=(targets, delay, send_o), daemon=True
        ).start()

    def abort(self):
        self.active = False
        self.discovery_active = False
        self.log("\n[System] Abort signal sent...")

    def _batch_thread(self, targets, delay, send_o):
        self.log(f"\n--- BATCH STARTED: {len(targets)} faults ---")
        for idx, cmd in enumerate(targets):
            if not self.active or not self.serial.is_connected:
                break

            self.log(f"\n[Batch #{idx+1}/{len(targets)}] Injecting...")
            self.serial.write(("I" + self.endline).encode("ascii"))
            time.sleep(0.2)
            self.serial.write((cmd + self.endline).encode("ascii"))
            time.sleep(delay)

            if send_o:
                self.serial.write(("O" + self.endline).encode("ascii"))
                time.sleep(delay)

            self.update_progress(idx + 1)

        self.active = False
        self.log("\n--- BATCH FINISHED/ABORTED ---")
        self.on_complete()

    # --- Discovery Engine ---
    def start_discovery(self, targets, delay, endline):
        self.discovery_targets = targets
        self.delay = delay
        self.endline = endline
        self.discovery_active = True
        self.discovery_idx = 0
        self.log("\n--- DISCOVERY MODE STARTED ---")
        self._disc_inject()

    def _disc_inject(self):
        if self.discovery_idx >= len(self.discovery_targets):
            self.log("\n[Discovery] List complete.")
            self.discovery_active = False
            self.on_complete()
            return

        cmd = self.discovery_targets[self.discovery_idx]
        self.log(
            f"\n[Discovery #{self.discovery_idx+1}/{len(self.discovery_targets)}] Paused at: {cmd}"
        )
        self.serial.write(("I" + self.endline).encode("ascii"))
        time.sleep(0.2)
        self.serial.write((cmd + self.endline).encode("ascii"))

    def save_and_next(self):
        cmd = self.discovery_targets[self.discovery_idx]
        with open("golden_faults.txt", "a") as f:
            f.write(f"{cmd}\n")
        self.log(f"[Saved] Logged fault to golden_faults.txt")
        self._disc_next()

    def skip_and_next(self):
        self.log(f"[Skipped] Moving to next fault.")
        self._disc_next()

    def _disc_next(self):
        self.serial.write(("O" + self.endline).encode("ascii"))
        time.sleep(self.delay)
        self.discovery_idx += 1
        self._disc_inject()

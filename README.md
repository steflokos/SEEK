# S.E.E.K. - Soft Error Exploration Kit

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**S.E.E.K.** (Soft Error Exploration Kit) is a modular automation engine designed for Soft Error Mitigation (SEM) and Single Event Upset (SEU) fault injection testing. Built for reproducibility and precision, it provides an integrated environment to map, manage, and execute fault injection campaigns on target hardware via UART incorporated in Xilinx's SEM IP.

## Table of Contents

- [Key Features](#-key-features)
- [Methodology: How S.E.E.K. Works](#-methodology-how-seek-works)
- [Software Architecture](#-software-architecture)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [License](#-license)

## Key Features

### 1. Advanced Target Management
- **Architecture Awareness:** Dynamically adjusts words-per-frame and bitwise pipeline offsets depending on the selected target FPGA (7-Series, UltraScale, or UltraScale+).
- **Bitstream Mapping:** Automatically correlates Logic Location (`.ll`) and Essential Bit Data (`.ebd`) files to extract precise fault targets for specific IP cores.
- **Integrated Editor:** A built-in code-style editor with line numbering for manual review and modification of injection targets.

### 2. Robust Execution Engine
- **Batch Injection:** Automates the injection of hundreds of faults with configurable delay intervals.
- **Auto-Scrubbing Logic:** Optional automated "Scrub" (Send 'O') sequence after each injection to restore hardware state.
- **Real-time Progress:** Visual tracking of campaign status and injection throughput.

### 3. Discovery Mode (Golden Fault Identification)
- **Interactive Exploration:** Step through potential fault locations manually.
- **Fault Logging:** Identify and save "Golden Faults" (critical failures) to a persistent `golden_faults.txt` log for deeper analysis.
- **Skip Logic:** Quickly bypass non-critical or redundant bit locations during discovery.

### 4. Integrated Monitoring & Control
- **Live Terminal:** A high-performance, read-only log monitor for incoming SEM data, operating on a background thread to prevent UI freezing.
- **Customizable Endlines:** Selectable serial terminations (CRLF, CR, LF, None) to match your specific SEM controller requirements.
- **Manual Command Line:** A dedicated command interface for sending real-time, low-level instructions to hardware without interrupting automated processes.

## Methodology: How S.E.E.K. Works

S.E.E.K. uses a specialized "Frame-Level Mapping" strategy to identify configuration bits vulnerable to Single Event Upsets (SEUs). Unlike standard scripts that only look for explicitly named elements, S.E.E.K. explores the physical architecture of the FPGA to find hidden logic.

### The Frame-Level Strategy
Standard Vivado Logic Allocation (`.ll`) files often only provide names for "architectural" elements like Flip-Flops or BRAM. They frequently leave the configuration bits for Look-Up Tables (LUTs)-the actual gates performing the logic-unnamed or "anonymous."

S.E.E.K. overcomes this by identifying the Frame Addresses (FAR) where the target IP resides and then scanning the entire physical frame for any bit marked as "Essential" by the Vivado Essential Bits (`.ebd`) file.

### Architecture-Specific Pipeline Offsets & Parsing
Different Xilinx FPGA families structure their bitstreams differently. S.E.E.K. dynamically accounts for these architectural shifts:
1. **Clean EBD Parsing:** The `.ebd` files often contain header metadata (dates, version numbers) that include `0`s and `1`s. S.E.E.K. utilizes a strict regex parser (`r"[01]{16,}"`) to completely ignore the header and only read the pure 32-bit data payloads.
2. **Pipeline Adjustments:** When calculating the absolute starting bit position of a frame in the bitstream, the tool automatically shifts the index to account for the FPGA's pipeline words:
   - **7-Series (Artix/Kintex):** 0 pipeline words.
   - **UltraScale:** 10 pipeline words.
   - **UltraScale+:** 25 pipeline words.

### The 3-Step Execution Flow

#### 1. Frame Identification
The engine scans the `.ll` file for the hierarchical name of the target IP (e.g., `design_1_i/c_addsub_0`). It extracts every unique Frame Address (FAR) associated with that logic.

#### 2. Essential Bit Cross-Referencing
For every discovered frame, S.E.E.K. calculates the starting position of that frame within the global bitstream (accounting for architecture offsets). It then scans all necessary bits of the frame against the `.ebd` file. If a bit is marked with a '1', it is identified as a target.

#### 3. Command Generation
For every essential bit found, the tool automatically constructs a 40-bit **Physical Frame Address** (PFA) injection command. The bitwise math precisely packs the 25-bit Frame Address (FAR) and the specific bit coordinates into the required Xilinx Specification:

```

Bit [39]: Hardcoded to 0 to signal a Physical Frame Address command.
Bits (SS): Hardware SLR number for SSI; set to 00 for non-SSI monolithic devices.
Bits: The 25-bit FAR value, which encapsulates the following sub-fields:
TT: Block type (2-bit).
H: Half address (1-bit).
RRRRR: Row address (5-bit).
CCCCCCCCCC: Column address (10-bit).
MMMMMMM: Minor address (7-bit).
Bits [11:5] (WWWWWWW): The 7-bit Word address within the frame.
Bits [4:0] (BBBBB): The 5-bit Bit address within the word.

```

### Why It Is More Accurate
By targeting the entire frame, S.E.E.K. captures the "latent" logic of the design—the LUT truth tables and interconnect MUXes that standard scripts often miss. This ensures a much higher success rate in finding "Golden Faults" that actually trigger functional failures. *(Note: It is common for only 5% to 15% of the bits identified as essential to actually cause an observable failure during a specific test run).*

## Software Architecture

S.E.E.K. utilizes a modular, decoupled architecture to ensure UI responsiveness and easy maintenance:
* `main.py` - The entry point that initializes the application.
* `gui.py` - Handles the Tkinter layout, dynamic dropdowns, and user interactions.
* `hardware.py` - Manages the UART connection and continuous background reading loop.
* `campaign.py` - Controls the timing, threading, and sequence logic for Batch and Discovery modes.
* `mapper.py` - A pure mathematical engine for parsing `.ll`/`.ebd` files and processing bitwise PFA calculations.

## Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Hardware Interface:** A serial connection (UART) to a device running a SEM-capable controller.

### Dependencies
Install the required serial library:

```bash
pip3 install pyserial
```

### Running the Engine

Because the application is modular, you must run it from the main entry point, inside the *seek_engine* folder:

```bash
python3 main.py
```

## Usage Guide

### Mapping Targets

1. **Browse** for your design's `.ll` and `.ebd` files.
2. Select your **Arch** (Architecture) to automatically set the correct Words/Frame and pipeline offsets.
3. Specify the **Target IP** string (e.g., `design_1_i/my_ip_0`).
4. Click **Extract Bits to Editor** to generate the injection list.
5. *Alternatively*, load a golden samples .txt file, containing previously identified and constructed injection commands

### Connecting Hardware

1. Select the appropriate **COM Port**, **New Line** termination (e.g., CRLF), and **Baud Rate**.
2. Click **Connect UART**. The system status will update in the Live Terminal.

### Running a Campaign

1. Set the **Injection Delay** (the time the system waits to observe the fault's effect).
2. Enable **Auto-Scrub** if you want to send a reset/fix command between injections.
3. Click **Run Target List** to begin automation, or **Start Discovery Mode** for manual stepping.

## License

This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/license/mit) file for details.

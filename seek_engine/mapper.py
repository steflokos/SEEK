import os
import re

def extract_targets(ll_path, ebd_path, target_ip, words, architecture):
    """Parses LL and EBD files to extract target addresses based on Architecture."""
    if not os.path.exists(ll_path) or not os.path.exists(ebd_path):
        raise FileNotFoundError("Valid .ll and .ebd files required for mapping.")

    # Safely read EBD file, skipping any 0s and 1s in the header text
    ebd_bits = []
    with open(ebd_path, "r") as f:
        for line in f:
            clean_line = line.strip()
            # Only match lines that are exclusively 0s and 1s and sufficiently long.
            # Standard Xilinx payload lines are exactly 32 bits long.
            if re.fullmatch(r"[01]{16,}", clean_line):
                ebd_bits.append(clean_line)
    
    ebd_data = "".join(ebd_bits)

    # Extract FARs belonging to the Target IP
    t_fars = set()
    with open(ll_path, "r") as f:
        for line in f:
            if "Bit " in line and target_ip.lower() in line.lower():
                t_fars.add(line.split()[2])

    # Map FARs to absolute starting bit positions
    far_to_abs = {}
    with open(ll_path, "r") as f:
        for line in f:
            if "Bit " in line:
                p = line.split()
                if p[2] in t_fars:
                    far_to_abs[p[2]] = int(p[1]) - int(p[3])

    # Determine Architecture Pipeline Offset
    pipeline_words = 0
    if architecture == "UltraScale":
        pipeline_words = 10
    elif architecture == "UltraScale+":
        pipeline_words = 25
    # 7-Series (Artix/Kintex) defaults to 0

    # Convert words to total bit offset (1 word = 32 bits)
    pipeline_offset_bits = pipeline_words * 32

    # Extract Valid Targets
    targets = []
    for far, start_pos in far_to_abs.items():
        for bit_idx in range(words * 32):
            
            # Shift the absolute position by the architecture pipeline offset
            abs_pos = start_pos + bit_idx + pipeline_offset_bits
            
            if abs_pos < len(ebd_data) and ebd_data[abs_pos] == "1":
                
                # The PFA format logic remains the same across all three architectures
                pfa_int = (
                    ((int(far, 16) & 0x3FFFFFF) << 12)
                    | ((bit_idx // 32 & 0x7F) << 5)
                    | (bit_idx % 32 & 0x1F)
                )

                targets.append(f"N {pfa_int:010X}")

    return targets
import os
import re


def extract_targets(ll_path, ebd_path, target_ip, words, architecture, neighbor_frames):
    """Parses LL and EBD files to extract target addresses based on Architecture and Neighbor proximity."""
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
    frame_bits = words * 32

    # Extract Valid Targets
    targets = []
    processed_frames = (
        set()
    )  # Track generated FARs to prevent duplicate faults on overlapping neighbors

    for base_far, base_start_pos in far_to_abs.items():
        base_far_int = int(base_far, 16)

        # Iterate from -neighbor_frames to +neighbor_frames
        for offset in range(-neighbor_frames, neighbor_frames + 1):

            # Calculate the neighbor's FAR and Bitstream Position
            neighbor_far_int = base_far_int + offset

            # Skip if we already mapped this exact frame from another nearby target
            if neighbor_far_int in processed_frames:
                continue
            processed_frames.add(neighbor_far_int)

            neighbor_start_pos = base_start_pos + (offset * frame_bits)

            # Ensure we don't accidentally index outside the bounds of the EBD file
            if neighbor_start_pos < 0 or neighbor_start_pos >= len(ebd_data):
                continue

            # Process the Frame
            for bit_idx in range(frame_bits):
                abs_pos = neighbor_start_pos + bit_idx + pipeline_offset_bits

                if 0 <= abs_pos < len(ebd_data) and ebd_data[abs_pos] == "1":

                    pfa_int = (
                        ((neighbor_far_int & 0x3FFFFFF) << 12)
                        | ((bit_idx // 32 & 0x7F) << 5)
                        | (bit_idx % 32 & 0x1F)
                    )

                    targets.append(f"N {pfa_int:010X}")

    return targets

import os
import re

def extract_targets(ll_path, ebd_path, target_ip, words):
    """Parses LL and EBD files to extract target addresses."""
    if not os.path.exists(ll_path) or not os.path.exists(ebd_path):
        raise FileNotFoundError("Valid .ll and .ebd files required for mapping.")
        
    with open(ebd_path, 'r') as f:
        ebd_data = re.sub(r'[^01]', '', f.read())
        
    t_fars = set()
    with open(ll_path, 'r') as f:
        for line in f:
            if "Bit " in line and target_ip.lower() in line.lower():
                t_fars.add(line.split()[2])
                
    far_to_abs = {}
    with open(ll_path, 'r') as f:
        for line in f:
            if "Bit " in line:
                p = line.split()
                if p[2] in t_fars:
                    far_to_abs[p[2]] = int(p[1]) - int(p[3])

    targets = []
    for far, start_pos in far_to_abs.items():
        for bit_idx in range(words * 32):
            abs_pos = start_pos + bit_idx
            if abs_pos < len(ebd_data) and ebd_data[abs_pos] == '1':
                pfa_int = ((int(far, 16) & 0x3FFFFFF) << 12) | ((bit_idx // 32 & 0x7F) << 5) | (bit_idx % 32 & 0x1F)
                targets.append(f"N {pfa_int:010X}")
                
    return targets
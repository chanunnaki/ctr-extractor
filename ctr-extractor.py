import os
import sys
import hashlib

# Expected MD5 of the CTR NTSC-U (USA) retail redump bin file
EXPECTED_MD5 = "ab95bfca8a4bb3d90daa6519acf6e944"

# Sector size constants
BIN_SECTOR_SIZE = 2352
ISO_USER_DATA_SIZE = 2048
HEADER_OFFSET = 24

def calculate_md5(file_path):
    print("Calculating MD5 hash to verify disc image...")
    hash_md5 = hashlib.md5()
    total_size = os.path.getsize(file_path)
    processed = 0
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096 * 1024), b""):
            hash_md5.update(chunk)
            processed += len(chunk)
            print(f"Hashing: {processed * 100 // total_size}% complete...", end="\r")
    print()
    return hash_md5.hexdigest()

def read_sector(f_bin, sector_num):
    f_bin.seek(sector_num * BIN_SECTOR_SIZE + HEADER_OFFSET)
    return f_bin.read(ISO_USER_DATA_SIZE)

def read_le32(buf, offset):
    return int.from_bytes(buf[offset:offset+4], 'little')

def parse_directory(f_bin, start_sector, data_length):
    records = []
    remaining = data_length
    sector = start_sector
    
    while remaining > 0:
        sector_data = read_sector(f_bin, sector)
        offset = 0
        while offset < ISO_USER_DATA_SIZE:
            rec_len = sector_data[offset]
            if rec_len == 0:
                # Reached sector padding / end of records in this sector
                break
                
            # Parse record properties
            extent = read_le32(sector_data, offset + 2)
            size = read_le32(sector_data, offset + 10)
            flags = sector_data[offset + 25]
            name_len = sector_data[offset + 32]
            name_bytes = sector_data[offset + 33 : offset + 33 + name_len]
            name = name_bytes.decode('ascii', errors='ignore')
            
            # Clean up ISO 9660 version suffix (e.g. "BIGFILE.BIG;1" -> "BIGFILE.BIG")
            if ';' in name:
                name = name.split(';')[0]
                
            # Skip current (0) and parent (1) directory markers
            if name_len > 0 and sector_data[offset + 33] not in (0, 1):
                records.append({
                    'name': name,
                    'extent': extent,
                    'size': size,
                    'is_dir': bool(flags & 2)
                })
                
            offset += rec_len
            
        remaining -= ISO_USER_DATA_SIZE
        sector += 1
        
    return records

def extract_file(f_bin, start_sector, file_size, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f_out:
        remaining = file_size
        sector = start_sector
        while remaining > 0:
            sector_data = read_sector(f_bin, sector)
            chunk_size = min(remaining, ISO_USER_DATA_SIZE)
            f_out.write(sector_data[:chunk_size])
            remaining -= chunk_size
            sector += 1

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ctr-extractor.py <path_to_ctr_game.bin> [output_directory]")
        sys.exit(1)
        
    bin_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_assets"
    
    if not os.path.exists(bin_path):
        print(f"Error: File '{bin_path}' not found.")
        sys.exit(1)
        
    # 1. Hash Check
    file_md5 = calculate_md5(bin_path)
    print(f"File MD5: {file_md5}")
    if file_md5 == EXPECTED_MD5:
        print("✓ MD5 matches official Crash Team Racing (USA) retail disc!")
    else:
        print("⚠️ Warning: MD5 does not match the official NTSC-U v1.0 redump.")
        print(f"Expected: {EXPECTED_MD5}")
        choice = input("Do you want to proceed anyway? (y/n): ")
        if choice.lower() not in ('y', 'yes'):
            sys.exit(0)
            
    print(f"Extracting assets to: {output_dir}")
    
    # 2. Parse ISO structure and extract
    with open(bin_path, "rb") as f_bin:
        # PVD (Primary Volume Descriptor) is always at sector 16
        pvd_sector = 16
        pvd = read_sector(f_bin, pvd_sector)
        
        # Verify it's an ISO 9660 PVD
        if pvd[1:6] != b'CD001':
            print("Error: The file is not a valid ISO 9660 image.")
            sys.exit(1)
            
        # Root Directory Record is at offset 156 in the PVD
        root_rec_offset = 156
        root_extent = read_le32(pvd, root_rec_offset + 2)
        root_size = read_le32(pvd, root_rec_offset + 10)
        
        # Files we want to extract for ctr-native
        target_files = {
            "BIGFILE.BIG": "BIGFILE.BIG",
            "TEST.STR": "TEST.STR",
            "SOUNDS/KART.HWL": "SOUNDS/KART.HWL",
            "XA": "XA"  # The whole folder
        }
        
        def walk_and_extract(sector, size, current_path=""):
            records = parse_directory(f_bin, sector, size)
            for rec in records:
                rel_path = f"{current_path}/{rec['name']}".strip("/")
                
                # Check if this item matches any of our targets
                should_extract = False
                for target, dest_subpath in target_files.items():
                    if rel_path == target or rel_path.startswith(target + "/"):
                        should_extract = True
                        break
                        
                if should_extract:
                    dest_path = os.path.join(output_dir, rel_path)
                    if rec['is_dir']:
                        print(f"Entering directory: {rel_path}")
                        walk_and_extract(rec['extent'], rec['size'], rel_path)
                    else:
                        print(f"Extracting: {rel_path} ({rec['size']:,} bytes)...")
                        extract_file(f_bin, rec['extent'], rec['size'], dest_path)
                elif rec['is_dir']:
                    # Even if not directly a target folder, walk it to find sub-targets
                    walk_and_extract(rec['extent'], rec['size'], rel_path)
                    
        walk_and_extract(root_extent, root_size)
        
    print(f"✓ Extraction complete! Assets are saved in: {output_dir}")

if __name__ == "__main__":
    main()

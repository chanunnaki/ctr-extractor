# CTR Asset Extractor

A simple, self-contained Python script to extract assets from a retail *Crash Team Racing* (PS1) NTSC-U ROM directly, without needing to mount disc images or install external dependencies.

This is designed for use with the [CTR-tools/ctr-native](https://github.com/CTR-tools/ctr-native) PC port project.

## Expected ROM Details
The script is configured to look for the clean NTSC-U (USA) v1.0 release:
* **Game**: Crash Team Racing (PS1, 1999)
* **Region**: NTSC-U (USA) v1.0
* **Disc Serial**: `SCUS-944.26`
* **Expected MD5 Checksum**: `ab95bfca8a4bb3d90daa6519acf6e944`

## How to Use

1. Copy `ctr-extractor.py` to a folder on your machine.
2. Put your Crash Team Racing `.bin` and `.cue` files in the **same directory** as the script.
3. Open a terminal in that directory and run:

```bash
python3 ctr-extractor.py "CTR - Crash Team Racing (USA).bin" assets
```

This will verify the game's MD5 checksum and extract the required game assets into an `assets/` folder. You can then copy or move this `assets/` folder to your compiled `ctr-native` directory to run the game!

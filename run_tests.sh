#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 verification/generate_vectors.py
mkdir -p build/obj_dir
verilator --binary --timing --trace -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL --top-module ecg_tb \
  --Mdir build/obj_dir src/project.v verification/ecg_tb.sv
./build/obj_dir/Vecg_tb

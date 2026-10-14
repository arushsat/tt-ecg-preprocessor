# How it works

An educational digital preprocessor for externally digitized ECG-like samples.
It computes a four-sample moving average with signed 8-bit inputs and outputs.
It does not acquire analog signals or run an AI model. Any sensor amplifier,
ADC, sample scaling, and downstream model run outside this block.

## Specification

At each accepted sample x[n], output y[n] = floor((x[n] + x[n-1] +
x[n-2] + x[n-3]) / 4). The three previous samples start at zero after reset.
The accumulator is signed 10-bit: its range is -512 through 508, so addition
does not overflow. Output range is -128 through 127. There is no saturation.
Negative rounding is toward negative infinity, so -1 / 4 becomes -1.

A transfer happens on a rising clock edge when BOTH valid and ready are high.
The input history advances only on accepted transfers, not every clock.
An accepted input creates a registered result immediately after that edge.
The earliest that result can be consumed is the next rising edge. With a
continuously ready consumer, one input and one output can transfer every cycle
(after the initial latency). The clock target in info.yaml is 10 MHz; it is
an unverified implementation target, not a measured maximum clock rate.

There is one output slot. When it is occupied and output_ready is low,
input_ready goes low and the result is held. When a result is consumed and
a new sample is accepted at the same edge, the slot is replaced with the new
result. The producer must hold sample and input_valid until input_ready is
high at an edge. The consumer must only interpret data when output_valid is
high. All inputs must be synchronous to clk; no clock-domain crossing is built in.

rst_n is active-low and synchronous: hold it low across at least one rising
edge. It clears history, output data, and the occupied flag, even when ena is
low. Reset discards pending data. Ready/valid are masked while reset is low.
When ena is low, registers freeze and ready/valid are masked low; a pending
result becomes visible again when ena is high. Output data may retain its
last value while invalid; that value is not a new result.

## Pin mapping

| Pins | Direction | Meaning |
| --- | --- | --- |
| ui_in[7:0] | Input | Signed two's-complement sample |
| uo_out[7:0] | Output | Signed two's-complement average |
| uio[0] | Input | input_valid |
| uio[1] | Input | output_ready |
| uio[2] | Output | input_ready |
| uio[3] | Output | output_valid |
| uio[7:4] | Input/unused | Ignore; output drivers disabled |
| clk | Input | System clock |
| rst_n | Input | Synchronous active-low reset |
| ena | Input | Design enable |

uio_oe is always 0x0c. Unused output bits are zero.

## How to test

Run bash run_tests.sh from the package root. The Python model writes vectors;
the SystemVerilog testbench checks all output pins before and after each clock
edge. Tests cover startup, impulse, signed rounding, extrema, all 256 constant
input values, stalls, enable gating, resets, and deterministic random traffic.
The VCD waveform is verification/ecg.vcd. A VCD is a simulation waveform, not
a physical layout.

## External hardware

For a later demonstration, a microcontroller can replay scaled signed samples
using the synchronous handshake interface. This version contains no SPI, UART,
ADC or electrode interface. Use synthetic or recorded data first. The averaging
filter can alter ECG morphology; no clinical utility or improved AI accuracy
has been established. Compare downstream model quality before claiming benefit.

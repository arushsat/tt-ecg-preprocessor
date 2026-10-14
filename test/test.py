from pathlib import Path

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_ecg_preprocessor(dut):
    vector_file = (
        Path(__file__).resolve().parent.parent
        / "verification"
        / "vectors.txt"
    )

    rows = [
        tuple(map(int, line.split()))
        for line in vector_file.read_text().splitlines()
        if line.strip()
    ]

    assert len(rows) == 11122, "Missing or truncated test vectors"
    assert all(len(row) == 11 for row in rows), "Malformed vector row"

    def check_outputs(ready, valid, data, cycle, phase):
        expected_pins = (valid << 3) | (ready << 2)

        assert int(dut.uio_oe.value) == 0x0C, (
            f"Cycle {cycle}, {phase}: incorrect pin directions"
        )
        assert int(dut.uio_out.value) == expected_pins, (
            f"Cycle {cycle}, {phase}: incorrect ready/valid outputs"
        )
        assert int(dut.uo_out.value) == data, (
            f"Cycle {cycle}, {phase}: "
            f"expected data {data}, got {int(dut.uo_out.value)}"
        )

    # Establish a known state with a synchronous reset.
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(5, unit="us")
    dut.clk.value = 1
    await Timer(5, unit="us")
    dut.clk.value = 0

    for cycle, row in enumerate(rows):
        (
            reset_n, enable, sample, input_valid, output_ready,
            before_ready, before_valid, before_data,
            after_ready, after_valid, after_data,
        ) = row

        # Drive inputs while the clock is low.
        dut.rst_n.value = reset_n
        dut.ena.value = enable
        dut.ui_in.value = sample
        dut.uio_in.value = input_valid | (output_ready << 1)

        await Timer(4, unit="us")
        check_outputs(
            before_ready, before_valid, before_data,
            cycle, "before rising edge",
        )

        await Timer(1, unit="us")
        dut.clk.value = 1

        # Allow the registered result and combinational outputs to settle.
        await Timer(1, unit="us")
        check_outputs(
            after_ready, after_valid, after_data,
            cycle, "after rising edge",
        )

        await Timer(4, unit="us")
        dut.clk.value = 0

    dut._log.info(
        "PASS: %d cycles matched the Python reference model", len(rows)
    )
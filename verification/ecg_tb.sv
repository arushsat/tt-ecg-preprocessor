`timescale 1ns/1ps
module ecg_tb;
    logic clk = 0;
    logic rst_n = 0, ena = 0;
    logic [7:0] ui_in = 0, uio_in = 0;
    wire [7:0] uo_out, uio_out, uio_oe;
    tt_um_arush_ecg_preprocessor dut (.*);
    integer fd, rc, n = 0;
    integer rn, en, sample_in, iv, ordy;
    integer br, bv, bd, ar, av, ad;
    task automatic check_outputs(input integer r, v, d);
        if (uio_out[2] !== (r != 0) || uio_out[3] !== (v != 0)
            || uo_out !== d[7:0] || uio_oe !== 8'h0c
            || (uio_out & 8'hf3) !== 8'h00)
            $fatal(1, "Cycle %0d: got ready=%b valid=%b data=%0d; expected %0d %0d %0d",
                   n, uio_out[2], uio_out[3], $signed(uo_out), r, v, d);
    endtask
    initial begin
        $dumpfile("verification/ecg.vcd");
        $dumpvars(0, ecg_tb);
        // Initial reset edge establishes defined state before checking vectors.
        #5; clk = 1; #5; clk = 0;
        fd = $fopen("verification/vectors.txt", "r");
        if (fd == 0) $fatal(1, "Run python3 verification/generate_vectors.py first");
        rc = $fscanf(fd, "%d %d %d %d %d %d %d %d %d %d %d",
                     rn,en,sample_in,iv,ordy,br,bv,bd,ar,av,ad);
        while (rc == 11) begin
            rst_n = (rn != 0); ena = (en != 0);
            ui_in = sample_in[7:0];
            uio_in = {6'b0, (ordy != 0), (iv != 0)};
            #4; check_outputs(br,bv,bd);
            #1; clk = 1;
            #1; check_outputs(ar,av,ad);
            #4; clk = 0;
            n = n + 1;
            rc = $fscanf(fd, "%d %d %d %d %d %d %d %d %d %d %d",
                         rn,en,sample_in,iv,ordy,br,bv,bd,ar,av,ad);
        end
        if (!$feof(fd) || n != 11122)
            $fatal(1, "Malformed or truncated vector file: checked %0d cycles", n);
        $fclose(fd);
        $display("PASS: %0d cycles matched the Python reference model", n);
        $finish;
    end
endmodule

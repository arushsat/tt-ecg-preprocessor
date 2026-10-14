// SPDX-License-Identifier: Apache-2.0
`default_nettype none
`timescale 1ns/1ps
// Four-sample moving average with a one-entry elastic output register.
module tt_um_arush_ecg_preprocessor (
    input wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input wire ena,
    input wire clk,
    input wire rst_n
);
    reg signed [7:0] previous_1, previous_2, previous_3;
    reg [7:0] result;
    reg occupied;
    wire input_valid = uio_in[0];
    wire output_ready = uio_in[1];
    wire input_ready = rst_n && ena && (!occupied || output_ready);
    wire output_valid = rst_n && ena && occupied;
    // Explicit sign extension prevents 8-bit intermediate overflow.
    wire signed [9:0] sample_ext = {{2{ui_in[7]}}, ui_in};
    wire signed [9:0] old1_ext = {{2{previous_1[7]}}, previous_1};
    wire signed [9:0] old2_ext = {{2{previous_2[7]}}, previous_2};
    wire signed [9:0] old3_ext = {{2{previous_3[7]}}, previous_3};
    wire signed [9:0] sum = sample_ext + old1_ext + old2_ext + old3_ext;
    // Taking bits 9:2 implements signed division by four, rounded DOWN.
    always @(posedge clk) begin
        if (!rst_n) begin
            previous_1 <= 0;
            previous_2 <= 0;
            previous_3 <= 0;
            result <= 0;
            occupied <= 0;
        end else if (ena) begin
            if (input_valid && input_ready) begin
                previous_3 <= previous_2;
                previous_2 <= previous_1;
                previous_1 <= ui_in;
                result <= sum[9:2];
                occupied <= 1;
            end else if (output_ready) begin
                occupied <= 0;
            end
        end
    end
    assign uo_out = result;
    assign uio_out = {4'b0000, output_valid, input_ready, 2'b00};
    assign uio_oe = 8'b00001100;
    // Mark unconnected input pads as intentionally unused for lint.
    wire _unused = &{uio_in[7:2], sum[1:0], 1'b0};
endmodule
`default_nettype wire

module iverilog_dump();
initial begin
    $dumpfile("axis_sync_fifo.fst");
    $dumpvars(0, axis_sync_fifo);
end
endmodule

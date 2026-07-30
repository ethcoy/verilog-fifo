module iverilog_dump();
initial begin
    $dumpfile("axis_async_fifo.fst");
    $dumpvars(0, axis_async_fifo);
end
endmodule

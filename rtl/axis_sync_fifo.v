module axis_sync_fifo #(
    parameter c_DATA_WIDTH = 16,
    parameter c_FIFO_DEPTH = 32
) (
    input wire i_clk,
    input wire i_rst,

    input wire [c_DATA_WIDTH - 1:0] s_axis_tdata,
    input wire s_axis_tvalid,
    output wire s_axis_tready,
    input wire s_axis_tlast,

    output wire [c_DATA_WIDTH - 1:0] m_axis_tdata,
    output wire m_axis_tvalid,
    input wire m_axis_tready,
    output wire m_axis_tlast
);

// +1 in size for tlast
localparam c_DATA_WIDTH_LST = c_DATA_WIDTH + 1'b1;
reg [c_DATA_WIDTH_LST - 1:0] r_fifo_data [0:c_FIFO_DEPTH - 1];

localparam c_ADDR_WIDTH = $clog2(c_FIFO_DEPTH);

reg [c_ADDR_WIDTH - 1 + 1:0] r_addr = {c_ADDR_WIDTH{1'b0}};

reg s_axis_tready_reg = 1'b0;

assign s_axis_tready = s_axis_tready_reg;

reg [c_DATA_WIDTH - 1:0] m_axis_tdata_reg = {c_DATA_WIDTH{1'b0}};
reg m_axis_tvalid_reg = 1'b0;
reg m_axis_tlast_reg = 1'b0;

assign m_axis_tdata = m_axis_tdata_reg;
assign m_axis_tvalid = m_axis_tvalid_reg;
assign m_axis_tlast = m_axis_tlast_reg;

always @(*) begin
    s_axis_tready_reg = 1'b1;
    m_axis_tvalid_reg = 1'b0;
    if (r_addr != {c_ADDR_WIDTH{1'b0}}) begin
        m_axis_tvalid_reg = 1'b1;
    end

    if (r_addr == c_FIFO_DEPTH) begin
        s_axis_tready_reg = 1'b0;
    end

    if (m_axis_tvalid && m_axis_tready) begin
        s_axis_tready_reg = 1'b1;
    end
end

integer i;

always @(posedge i_clk) begin
    if (s_axis_tvalid && s_axis_tready) begin
        if (r_addr == {c_ADDR_WIDTH{1'b0}}) begin
            m_axis_tdata_reg <= s_axis_tdata;
            m_axis_tlast_reg <= s_axis_tlast;
        end
        r_fifo_data[r_addr] <= {s_axis_tlast, s_axis_tdata};
        r_addr <= r_addr + 1'b1;
    end 

    if (m_axis_tvalid && m_axis_tready) begin
        if (r_addr != {c_ADDR_WIDTH{1'b0}}) begin
            m_axis_tdata_reg <= r_fifo_data[1][c_DATA_WIDTH - 1:0];
            m_axis_tlast_reg <= r_fifo_data[1][c_DATA_WIDTH_LST - 1];
        end

        for (i = 0; i < c_FIFO_DEPTH - 1'b1; i = i + 1) begin
            r_fifo_data[i] <= r_fifo_data[i + 1];
        end
        r_addr <= r_addr - 1'b1;
    end

    if (s_axis_tvalid && s_axis_tready && m_axis_tvalid && m_axis_tready) begin
        if (r_addr == 1'b1) begin
            m_axis_tdata_reg <= s_axis_tdata;
            m_axis_tlast_reg <= s_axis_tlast;
        end
        r_fifo_data[r_addr - 1'b1] <= {s_axis_tlast, s_axis_tdata};
        r_addr <= r_addr;
    end

end

endmodule
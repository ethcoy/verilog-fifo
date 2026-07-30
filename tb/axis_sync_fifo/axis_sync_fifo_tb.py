"""

MIT License

Copyright (c) 2026 Ethan Coyle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import cocotb

import os
import random

from cocotb import simulator
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Edge, Event, Timer
from cocotb.queue import AbstractQueue, Queue
from cocotb.simtime import get_sim_time

from cocotb_test.simulator import run

import pytest

class axis_source:
    def __init__(self, s_clk, s_axis_tdata, s_axis_tvalid, s_axis_tready, s_axis_tlast=None):
        self.s_clk = s_clk
        self.s_axis_tdata = s_axis_tdata
        self.s_axis_tvalid = s_axis_tvalid
        self.s_axis_tready = s_axis_tready
        self.s_axis_tlast = s_axis_tlast
        self.s_axis_tdata_sent = []
        self.s_axis_tlast_sent = []
        self.tdata_queue = Queue()
        self.tlast_queue = Queue()
        self.tdata_present = Event()
        cocotb.start_soon(self.__axis_source__())
    def send_nowait(self, data):
        for i in range(len(data)):
            self.tdata_queue.put_nowait(data[i])
            if (i == len(data) - 1):
                self.tlast_queue.put_nowait(1)
            else:
                self.tlast_queue.put_nowait(0)
        self.tdata_present.set()
    async def __axis_source__(self):
        while (True):
            await self.tdata_present.wait()
            while (not self.tdata_queue.empty()):
                self.s_axis_tdata.value = self.tdata_queue.get_nowait()
                if (self.s_axis_tvalid != None):
                    self.s_axis_tvalid.value = 1
                last_indicator = self.tlast_queue.get_nowait()
                if (self.s_axis_tlast != None):
                    if (last_indicator == 1):
                        self.s_axis_tlast.value = 1
                    else:
                        self.s_axis_tlast.value = 0
                await RisingEdge(self.s_clk)
                while (not self.s_axis_tready.value):
                    await RisingEdge(self.s_clk)
                self.s_axis_tdata_sent.append(self.s_axis_tdata.value)
                if (self.s_axis_tlast != None):
                    self.s_axis_tlast_sent.append(self.s_axis_tlast.value)
            self.tdata_present.clear()
            if (self.s_axis_tvalid != None):
                self.s_axis_tvalid.value = 0
            if (self.s_axis_tlast != None):
                self.s_axis_tlast.value = 0

class axis_sink:
    def __init__(self, m_clk, m_axis_tdata, m_axis_tvalid, m_axis_tready, m_axis_tlast=None):
        self.m_clk = m_clk
        self.m_axis_tdata = m_axis_tdata
        self.m_axis_tvalid = m_axis_tvalid
        self.m_axis_tready = m_axis_tready
        self.m_axis_tready.value = 1
        self.m_axis_tlast = m_axis_tlast
        self.m_axis_tdata_read = []
        self.m_axis_tlast_read = []
        self.tready_queue = Queue()
        self.tready_present = Event()
        cocotb.start_soon(self.__axis_sink__())
        cocotb.start_soon(self.__axis_sink_tready_pattern__())
    def tready_pattern(self, pattern):
        for i in range(len(pattern)):
            self.tready_queue.put_nowait(pattern[i])
            self.tready_present.set()
    async def __axis_sink__(self):
        while (True):
            await RisingEdge(self.m_clk)
            # if (not self.m_axis_tvalid.value):
                # await RisingEdge(self.m_axis_tvalid)
            # await RisingEdge(self.m_clk)
            # while (self.m_axis_tvalid.value):
            if (self.m_axis_tvalid.value and self.m_axis_tready.value):
                self.m_axis_tdata_read.append(self.m_axis_tdata.value)
                if (self.m_axis_tlast != None):
                    self.m_axis_tlast_read.append(self.m_axis_tlast.value)
                # await RisingEdge(self.m_clk)
    async def __axis_sink_tready_pattern__(self):
        while (True):
            await self.tready_present.wait()
            while (not self.tready_queue.empty()):
                await RisingEdge(self.m_clk)
                self.m_axis_tready.value = self.tready_queue.get_nowait()
            self.tready_present.clear()
            await RisingEdge(self.m_clk)
            self.m_axis_tready.value = 1

# @cocotb.test()
# async def test_tlast_propagation(dut):
#     """ Test tha the tlast pattern that is sent into the FIFO is replicated on the output """

#     cocotb.start_soon(Clock(dut.i_clk, 10, unit='ns').start())

#     await RisingEdge(dut.i_clk)

#     src = axis_source(dut.i_clk, dut.s_axis_tdata, dut.s_axis_tvalid, dut.s_axis_tready, dut.s_axis_tlast)
#     snk = axis_sink(dut.i_clk, dut.m_axis_tdata, dut.m_axis_tvalid, dut.m_axis_tready, dut.m_axis_tlast)

#     data = []
#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         data.append(random.randint(0, 2**int(dut.c_DATA_WIDTH.value) - 1))

#     src.send_nowait(data)

#     tready_pattern = []
#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         tready_pattern.append(random.randint(0, 1))

#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         tready_pattern.append(0)

#     snk.tready_pattern(tready_pattern)

#     await Timer(1000000, unit='ns')

#     src_tlast = [int(i) for i in src.s_axis_tlast_sent]
#     snk_tlast = [int(i) for i in snk.m_axis_tlast_read]

#     assert src_tlast == snk_tlast, 'Sent tlast and received tlast do not match...'

# @cocotb.test()
# async def test_tdata_propagation(dut):
#     """ Test that the tdata pattern that is sent into the FIFO is replicated on the output """

#     cocotb.start_soon(Clock(dut.i_clk, 10, unit='ns').start())

#     await RisingEdge(dut.i_clk)

#     src = axis_source(dut.i_clk, dut.s_axis_tdata, dut.s_axis_tvalid, dut.s_axis_tready, dut.s_axis_tlast)
#     snk = axis_sink(dut.i_clk, dut.m_axis_tdata, dut.m_axis_tvalid, dut.m_axis_tready, dut.m_axis_tlast)

#     data = []
#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         data.append(random.randint(0, 2**int(dut.c_DATA_WIDTH.value) - 1))

#     src.send_nowait(data)

#     tready_pattern = []
#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         tready_pattern.append(random.randint(0, 1))

#     for i in range(10*int(dut.c_FIFO_DEPTH.value)):
#         tready_pattern.append(0)

#     snk.tready_pattern(tready_pattern)

#     await Timer(1000000, unit='ns')

#     src_tdata = [int(i) for i in src.s_axis_tdata_sent]
#     snk_tdata = [int(i) for i in snk.m_axis_tdata_read]

#     assert src_tdata == snk_tdata, 'Sent tlast and received tlast do not match...'

# @pytest.mark.parametrize(
#     "parameters", [{"c_DATA_WIDTH": "12, 8",
#                     "c_FIFO_DEPTH": "128"}]
# )
# def test(parameters):
#     run(
#         verilog_sources=[
#             "./../../rtl/axis_sync_fifo.v",
#         ],
#         toplevel="axis_sync_fifo",
#         module="axis_sync_fifo_tb",
#         # timescale = "1ns/1ps",
#         parameters=parameters,
#         extra_env=parameters,
#         sim_build="sim_build/",
#         waves = '1'
#         # seed = '0'
#         + "_".join(("{}={}".format(*i) for i in parameters.items())),
#     )

@cocotb.test()
async def axis_sync_fifo(dut):
    dut.i_rst.value = 0
    dut.i_clk.value = 0

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await RisingEdge(dut.i_clk)

    src = axis_source(dut.i_clk, dut.s_axis_tdata, dut.s_axis_tvalid, dut.s_axis_tready, dut.s_axis_tlast)
    snk = axis_sink(dut.i_clk, dut.m_axis_tdata, dut.m_axis_tvalid, dut.m_axis_tready, dut.m_axis_tlast)

    data = []
    for i in range(10*c_FIFO_DEPTH):
        data.append(random.randint(0, 2**c_DATA_WIDTH - 1))

    src.send_nowait(data)

    tready_pattern = []
    for i in range(10*c_FIFO_DEPTH):
        tready_pattern.append(random.randint(0, 1))
    snk.tready_pattern(tready_pattern)

    tready_pattern = []
    for i in range(10*c_FIFO_DEPTH):
        tready_pattern.append(0)
    snk.tready_pattern(tready_pattern)

    src.send_nowait(data)
    src.send_nowait(data[1:5])
    src.send_nowait(data[4:26])
    src.send_nowait(data[25:102])
    src.send_nowait(data[5:99])

    await Timer(1000000, unit='ns')

    src_tdata = [int(i) for i in src.s_axis_tdata_sent]
    src_tlast = [int(i) for i in src.s_axis_tlast_sent]

    snk_tdata = [int(i) for i in snk.m_axis_tdata_read]
    snk_tlast = [int(i) for i in snk.m_axis_tlast_read]

    print(src_tdata)
    print(src_tlast)
    print()
    print(snk_tdata)
    print(snk_tlast)

    assert src_tdata == snk_tdata, 'Sent tdata and received tdata do not match...'
    assert src_tlast == snk_tlast, 'Sent tlast and received tlast do not match...'


parameters = {}
parameters['c_DATA_WIDTH'] = 16
parameters['c_FIFO_DEPTH'] = 512

c_DATA_WIDTH = parameters['c_DATA_WIDTH']
c_FIFO_DEPTH = parameters['c_FIFO_DEPTH']

if __name__ == "__main__":
    run(verilog_sources = [
            './../../rtl/axis_sync_fifo.v',
        ],
        toplevel = "axis_sync_fifo",
        module = "axis_sync_fifo_tb",
        parameters = parameters,
        sim_build = "sim_build/",
        timescale = "1ns/1ps",
        force_compile = True,
        seed = int(0),
        waves = 1,
    )

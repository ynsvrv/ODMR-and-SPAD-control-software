#! /bin/bash
ghdl -a *.vhd
ghdl -e test_bench
ghdl -r test_bench --stop-time=2ms --vcd=waves.vcd
gtkwave waves.vcd

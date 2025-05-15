library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity controller is
	generic (
		NUM_CYCLES		: natural -- Number of readout cycles to be done before sending data to PC.
	);
	port (
		-- General
		CLK           : in  std_logic;
		RST           : in  std_logic;
		
		-- Internal communication between modules
		RST_counters	: out std_logic := '0';
		DATA_READY		: out std_logic := '0'
	);
end controller;

architecture behaviour of controller is
	signal cycle_counter		: natural := 0;

begin
	process(CLK)
	begin
		if rising_edge(CLK) then
			-- Reset
			if RST = '1' then
				DATA_READY <= '0';
				cycle_counter <= 0;
				RST_counters <= '1';
			elsif cycle_counter < NUM_CYCLES then
				-- Keep on counting
				cycle_counter <= cycle_counter + 1;
				DATA_READY <= '0';
				RST_counters <= '0';
			elsif cycle_counter = NUM_CYCLES then
				-- Reached NUM_CYCLES. Data is ready to be sent
				cycle_counter <= cycle_counter + 1;
				DATA_READY <= '1';
				RST_counters <= '0';
			else
				-- Buffer sender has had time to copy the data. Counter can now be reset to start the next counting period.
				DATA_READY <= '0';
				RST_counters <= '1';
				cycle_counter <= 0;
			end if;
			
		end if;
    end process;
end architecture behaviour;

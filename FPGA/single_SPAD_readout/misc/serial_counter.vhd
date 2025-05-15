-- Implementation of counter for one SPAD array.
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity serial_counter is
	generic (
		COUNTER_SIZE	: natural --Number of bits for each individual counter
	);
	port (
		clk          	: in  std_logic;
      reset        	: in  std_logic;
      serial_input 	: in  std_logic;
		load				: in	std_logic;
		counts_out		: out std_logic_vector(COUNTER_SIZE*16-1 downto 0) := (others => '0')
	);
end serial_counter;

architecture behaviour of serial_counter is
	signal readout_counter	: natural := 0; -- Tells of which SPAD within the array the current bit is.
	
	type t_counts_internal is array(0 to 15) of natural;
	signal counts_internal	: t_counts_internal := (others => 0);
	
	type t_state is (start_state, idle_state, alert_state, read_state);
	signal state	: t_state := start_state;
	
begin
	process(clk)
	begin
	if rising_edge(clk) then
		-- Reset
		if reset = '1' then
			counts_internal <= (others => 0);
			readout_counter <= 0;
			state <= start_state;
		end if;
		
		-- Finite State Machine
		case state is
			when start_state =>
				counts_internal <= (others => 0);
				readout_counter <= 0;
				-- Immediately go to idle state from here
				state <= idle_state;
				
			when idle_state => 
				readout_counter <= 0;
				if load = '0' then
					-- Load pulse has been sent.
					-- Note that the flag bit should already be active by the time this case activates.
					if serial_input = '1' then
						-- Flag bit has already arrived!
						state <= read_state;
					else
						-- Maybe the flag bit comes next cycle? Stay alert.
						--state <= alert_state;
						state <= idle_state;
					end if;
				else
					-- Nothing happens. Just keep chillin.
					state <= idle_state;
				end if;
			
			when alert_state =>
				-- When it reaches this state, the load pulse has been sent, and this module is waiting for the flag bit to arrive.
				readout_counter <= 0;
				if serial_input = '1' then
					-- This is the flagbit! Prepare for incoming data.
					state <= read_state;
				else
					-- Still nothing? Just go back to idle I guess.
					state <= idle_state;
				end if;
				
			when read_state =>
				-- When the FSM reaches this state, the flag bit has arrived, and the data bits need to be read.
				if readout_counter < 16 then
					if serial_input = '1' then
						-- This is a high data bit.
						counts_internal(readout_counter) <= counts_internal(readout_counter) + 1;
					else
						-- This is a low data bit.
						counts_internal(readout_counter) <= counts_internal(readout_counter);
					end if;
					
					readout_counter <= readout_counter + 1;
					state <= read_state;
				else
					-- Data transmission is over.
					state <= idle_state;
				end if;
		end case;
	end if;
	end process;
	
	-- Pass internal counters to output
	gen: for i in 0 to 15 generate
		counts_out((i+1)*COUNTER_SIZE-1 downto i*COUNTER_SIZE) <= std_logic_vector(to_unsigned(counts_internal(i), COUNTER_SIZE));
	end generate;

end architecture behaviour;
	
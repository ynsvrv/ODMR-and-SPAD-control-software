library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity controller is
	Generic (
		NUM_CYCLES							: natural; -- Number of readout cycles to be done before sending data to PC.
		QUENCH_WIDTH						: std_logic_vector(4 downto 0) := "01000"; -- LSb --- MSb. Width of the quenching pulse
		QUENCH_DELAY						: std_logic_vector(4 downto 0) := "01000"; -- LSb --- MSb. Delay of the quenching pulse
		COLLECTION_TIME_PER_READOUT	: natural := 16 --Number of clock cycles between clear and load, where photons are actively counted.
	);
	Port (
		-- General
		CLK           : in  std_logic;
		RST           : in  std_logic;
		
		-- Internal communication between modules
		--command			: in natural := 0;
		--start				: in std_logic := '0'; -- Will start data acquisition process
		RST_counters	: out std_logic := '0';
		DATA_READY		: out std_logic := '0';

		-- Chip signals
		LOAD			: out std_logic := '1';
		CLEAR			: out std_logic := '0';
		SI_w			: out std_logic := '0';
		SI_d			: out std_logic := '0';
		RST_chip		: out std_logic := '0'
	);
end controller;

architecture behaviour of controller is

	signal readout_cycle_counter	 	: natural := 0;
	signal start							: std_logic := '1';
	
	type t_state is (start_state, conf_state, standby_state, clear_state, collect_state, load_state, read_state);
	signal state : t_state := start_state;
	
	signal conf_counter		: natural := 0;
	signal read_counter		: natural := 0;
	signal collect_counter	: natural := 0;

begin

	process(CLK)
	begin
		if rising_edge(CLK) then
			-- Reset
			if RST = '1' then
				state <= start_state;
			end if;
			
			-- Finite State Machine
			case state is
				when start_state =>
					RST_counters <= '1';
					DATA_READY <= '0';
					LOAD <= '1';
					CLEAR <= '0';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '1';
					-- Reset counters of the other states
					conf_counter <= 0;
					read_counter <= 0;
					collect_counter <= 0;
					-- Immediately go to the next state
					state <= conf_state;
					
				when conf_state =>
					-- In this state, configuration of the quenching pulse width and delay are configured.
					RST_counters <= '0';
					DATA_READY <= '0';
					LOAD <= '1';
					CLEAR <= '0';
					RST_chip <= '0';
					if conf_counter = 0 then
						-- Send flag bits
						SI_w <= '1';
						SI_d <= '1';
						-- Manage state
						conf_counter <= conf_counter + 1;
						state <= conf_state;
					elsif conf_counter < 6 then
						-- Send data bits
						SI_w <= QUENCH_WIDTH(5 - conf_counter);
						SI_d <= QUENCH_DELAY(5 - conf_counter);
						-- Manage state
						conf_counter <= conf_counter + 1;
						state <= conf_state;
					else
						-- The counter has reached 6, which means it's time for the next state
						SI_w <= '0';
						SI_d <= '0';
						state <= standby_state;
					end if;
				
				when standby_state =>
					RST_counters <= '1';
					DATA_READY <= '0';
					LOAD <= '1';
					CLEAR <= '0';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '0';
					
					if start = '1' then
						-- Start a multi-measurement
						readout_cycle_counter <= 0;
						state <= clear_state;
					else
						state <= standby_state;
					end if;
					
				when clear_state =>
					-- This state sends a clear pulse.
					RST_counters <= '0';
					DATA_READY <= '0';
					LOAD <= '1';
					CLEAR <= '1';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '0';
					-- Go to next state immediately
					state <= collect_state;
					collect_counter <= 0;
					-- This is the start of a readout cycle. Update counter.
					readout_cycle_counter <= readout_cycle_counter + 1;
					
				when collect_state =>
					-- In this state, we simply wait, while photons are actively being counted.
					RST_counters <= '0';
					DATA_READY <= '0';
					LOAD <= '1';
					CLEAR <= '0';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '0';
					
					if collect_counter = COLLECTION_TIME_PER_READOUT then
						-- Time is up. Prepare for sending load pulse
						state <= load_state;
					else
						collect_counter <= collect_counter + 1;
					end if;
					
				when load_state =>
					-- This state sends a load pulse.
					RST_counters <= '0';
					DATA_READY <= '0';
					LOAD <= '0';
					CLEAR <= '0';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '0';
					-- Immediately go to next state
					state <= read_state;
					read_counter <= 0;
					
				when read_state =>
					RST_counters <= '0';
					LOAD <= '1';
					CLEAR <= '0';
					SI_w <= '0';
					SI_d <= '0';
					RST_chip <= '0';
					
					-- Wait 16 cycles before moving on, so that any previous serial readout is done.
					if read_counter = 16 then
						-- Alright. That's the end of one readout cycle.
						if readout_cycle_counter = NUM_CYCLES then
							-- All readouts have been done. Send DATA_READY signal and go back to standby.
							DATA_READY <= '1';
							--state <= standby_state;
							-- Redo configuring. This way, it doesn't matter if the chip is turned on after the FPGA.
							conf_counter <= 0;
							state <= conf_state;
						else
							-- This was not yet the last readout cycle. Restart cycle.
							DATA_READY <= '0';
							state <= clear_state;
						end if;
					else
						DATA_READY <= '0';
						read_counter <= read_counter + 1;
						state <= read_state;
					end if;
			end case;
		end if;
    end process;
end architecture behaviour;

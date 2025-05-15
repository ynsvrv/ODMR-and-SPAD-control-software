library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity SPI_buffer_sender is
	generic (
		COUNTER_SIZE	: natural --Number of bits for each individual counter
	);
	Port (
		CLK            	: in  std_logic;
		RST            	: in  std_logic;
		START_TRANSFER 	: in  std_logic;                     -- Start transfer signal
		DATA_IN    			: in  std_logic_vector(COUNTER_SIZE-1 downto 0); -- Data to transfer
		  
		-- Connections with SPI Master module
		DIN      : out  std_logic_vector(7 downto 0) := (others => '0'); -- data for transmission to SPI slave
      --DIN_ADDR : out  std_logic_vector(0 downto 0) := (others => '0');  -- SPI slave address
      DIN_LAST : out  std_logic := '0'; -- when DIN_LAST = 1, last data word, after transmit will be asserted CS_N
      DIN_VLD  : out  std_logic := '0'; -- when DIN_VLD = 1, data for transmission are valid
      DIN_RDY  : in std_logic -- when DIN_RDY = 1, SPI master is ready to accept valid data for transmission
	);
end entity;

architecture RTL of SPI_buffer_sender is

	signal word_counter  : natural := 0;     -- Word counter
	signal start_byte_counter : natural := 0; --Indicates whether it's still sending start bits, and how far it is
	signal data_buffer	: std_logic_vector(COUNTER_SIZE-1 downto 0) := (others => '0'); --Internal buffer to temporarily hold the data
	signal wait_for_transfer : std_logic := '0'; -- When this is high, a byte has been sent, and we need to wait before sending a new one again.
	signal data_byte		: std_logic_vector(7 downto 0);
	signal flag_byte_counter : natural := 0;
	signal delay_counter	: natural := 0;
	
	constant num_bytes	: natural := COUNTER_SIZE/8; -- Number of bytes in the data buffer.
	constant num_flag_bytes	: natural := COUNTER_SIZE/8; -- Number of bytes needed to signal start-of-frame.
	constant delay			: natural := 1000; -- Number of (system) clock cycles to wait between sending bytes.
	
	type t_state is (start_state, FF_state, prepare_state, send_state);
	signal state : t_state := start_state;

begin
	process(CLK)
	begin
		if rising_edge(CLK) then
			if RST = '1' then
				state <= start_state;
			else
				-- Reset the wait_for_transfer
				if DIN_RDY = '0' then
					wait_for_transfer <= '0';
				end if;
				
				-- FSM
				case state is
					when start_state =>
						word_counter <= 0;
						wait_for_transfer <= '0';
						DIN_LAST <= '0';
						DIN_VLD <= '0';
						DIN <= "00000000";
						flag_byte_counter <= 0;
						
						if START_TRANSFER = '1' then
							state <= FF_state;
							-- Copy all data to internal buffer
							data_buffer <= DATA_IN;
						else
							state <= start_state;
						end if;
						
					when FF_state =>
						DIN <= "11111111";
						DIN_LAST <= '0';
						
						if DIN_RDY = '1' and wait_for_transfer = '0' then
							if flag_byte_counter = num_flag_bytes then
								-- Those were all the flag bytes. Continue to next state.
								state <= prepare_state;
							else
								-- Not yet done with flag bytes
								-- Send start byte
								DIN_VLD <= '1';
								wait_for_transfer <= '1';
								flag_byte_counter <= flag_byte_counter + 1;
								state <= FF_state;
							end if;
						else
							-- Not ready to send the next byte.
							DIN_VLD <= '0';
							state <= FF_state;
						end if;
						
					when prepare_state =>
						DIN <= "00000000";
						DIN_LAST <= '0';
						data_byte <= data_buffer(num_bytes*8 - 1 - word_counter*8 downto num_bytes*8 - (word_counter + 1)*8);
						DIN_VLD <= '0';
						if DIN_RDY = '1' then
							if delay_counter = delay then
								state <= send_state;
								delay_counter <= 0;
							else
								delay_counter <= delay_counter + 1;
								state <= prepare_state;
							end if;
						else
							state <= prepare_state;
							delay_counter <= 0;
						end if;
					
					when send_state =>
						DIN <= data_byte;
						
						if DIN_RDY = '1' and wait_for_transfer = '0' then
							-- Send byte
							DIN_VLD <= '1';
							if word_counter = num_bytes-1 then
								DIN_LAST <= '1';
							else
								DIN_LAST <= '0';
							end if;
							
							-- Go back to request a new byte from the counter
							state <= prepare_state;
							delay_counter <= 0;
							
							if word_counter = num_bytes then
								-- All bytes have been send. Return to start.
								state <= start_state;
								--Ensure all signals are back where they should be.
								DIN_LAST <= '0';
								DIN_VLD <= '0';
							else
								-- Go on with the next byte
								wait_for_transfer <= '1';
								word_counter <= word_counter + 1;
							end if;
							
						else
							DIN_VLD <= '0';
							DIN_LAST <= '0';
						end if;
						
				end case;
			end if;
		end if;
	end process;
end architecture;

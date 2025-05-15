-- Simple counter for counting the photon events of one SPAD.
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter is
	generic (
		COUNTER_SIZE	: natural --Number of bits for each individual counter
	);
	port (
		clk          	: in  std_logic;
      reset        	: in  std_logic;
      input 			: in  std_logic;
		counts_out		: out std_logic_vector(COUNTER_SIZE-1 downto 0) := (others => '0')
	);
end counter;

architecture behaviour of counter is
	signal counts_internal 			: unsigned(COUNTER_SIZE-1 downto 0) := (others => '0');
	signal counts_internal_sync	: unsigned(COUNTER_SIZE-1 downto 0) := (others => '0');

begin
	-- Asynchronously count input. Otherwise, a pulse might already be gone by the time the next clock signal hits.
	process(input)
	begin
		if reset = '1' then
			counts_internal <= (others => '0');
		elsif (input'event and input = '1') then
			counts_internal <= counts_internal + 1;
		end if;
	end process;
	
	-- Synchronize counts_internal to the clock domain
	process(clk)
	begin
		if rising_edge(clk) then
			if reset = '1' then
				counts_internal_sync <= (others => '0');
			else
				-- Transfer asynchronous counter value to synchronized register
				counts_internal_sync <= counts_internal;
			end if;
		end if;
	end process;
	
	--Pass the synchronized internal counts onwards
	counts_out <= std_logic_vector(counts_internal_sync);
end architecture behaviour;
-- Module that recieves SPI bytes and makes the command number from it
-- Currently just passing on the byte, but should be expanded to multi-byte later
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity command_resciever is
	port (
		CLK			: in std_logic;
		RST			: in std_logic;
		DOUT			: in std_logic_vector(7 downto 0); -- From SPI master
		DOUT_VLD		: in std_logic; -- From SPI master
		command_out	: out natural := 0; -- Connect with controller
		start			: out std_logic := '0' -- Tells the controller to start measuring
	);
end entity;

architecture behaviour of command_resciever is
	signal number : std_logic_vector(7 downto 0); --Internal register

begin
	process(CLK)
	begin
		if(rising_edge(CLK)) then
			if RST = '1' then
				number <= (others => '0');
			elsif DOUT_VLD = '1' then
				number <= DOUT;
				start <= '1';
			else
				start <= '0';
			end if;
		end if;
	end process;

-- Output value of internal register
command_out <= to_integer(unsigned(number));
end architecture;
				
	
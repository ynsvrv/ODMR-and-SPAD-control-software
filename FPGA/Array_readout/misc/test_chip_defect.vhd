library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.MATH_REAL.ALL;

entity test_chip is
port (
	LOAD			: in std_logic;
	CLEAR			: in std_logic;
	SI_w			: in std_logic;
	SI_d			: in std_logic;
	RST_chip		: in std_logic;
	SOX			: out std_logic_vector(15 downto 0) := (others => '0');
	CLK_chip		: in std_logic
);
end entity;

architecture behaviour of test_chip is
	-- Test image
	constant test_SPAD_signal	: std_logic_vector(255 downto 0) :=
	"0000000000000000" &
	"0000000000000000" &
	"0000000000000000" &
	"0000000001011111" &
	"0001110000000100" &
	"0010001001000100" &
	"0100000101000100" &
	"0100000101000100" &
	"0100010101000100" &
	"0010001001000100" &
	"0001110101000100" &
	"0000000000000000" &
	"0000000000000000" &
	"0000000000000000" &
	"0000000000000000" &
	"0000000000000000";
	
	signal PISO_counter : natural := 17;

begin
	-- Mimic a basic SPAD signal	
	process(CLK_chip)
	begin
	-- After start bits, make a recognisable shape in the data.
	if(falling_edge(CLK_chip)) then
		if LOAD = '0' then
			-- Start the serial transmission
			-- Send flag bits
			SOX <= (others => '1');
			PISO_counter <= 0;
		end if;
		
--		-- Serial transmission logic
--		if PISO_counter = 0 then
--			-- Send start bits
--			SOX <= (others => '1');
--			PISO_counter <= PISO_counter + 1;
		if PISO_counter < 17 then
			-- Send the data bits
			for i in 0 to 15 loop --Loop through the rows (SPAD arrays)
				if not(i = 4) then
					SOX(i) <= test_SPAD_signal(16*i + PISO_counter-1);
				else
					SOX(i) <= '1';
				end if;
			end loop;
			PISO_counter <= PISO_counter + 1;
		else
			SOX(3 downto 0) <= (others => '0');
			SOX(4) <= '1';
			SOX(15 downto 5) <= (others => '0');
		end if;
	end if;
	end process;
end architecture;
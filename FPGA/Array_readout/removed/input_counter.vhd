library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.numeric_std.ALL;

entity input_counter is
	 generic (
		  COUNTER_SIZE	: natural := 8 --Number of bits for each individual counter
	 );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        input       : in  std_logic;
        count_out   : out std_logic_vector(COUNTER_SIZE-1 downto 0)
    );
end input_counter;

architecture behaviour of input_counter is
    signal count, new_count: unsigned(COUNTER_SIZE-1 downto 0);
    signal input_high: std_logic;
begin
    process (clk)
    begin
        if rising_edge(clk) then
            if (reset = '1') then
                count <= (others => '0');
                input_high <= '0';
            else
                if (input = '1') then
                    if (input_high = '0') then
                        count <= new_count;
                        input_high <= '1';
                    else
                        count <= count;
                        input_high <= input_high;
                    end if;
                else
                    count <= count;
                    input_high <= '0';
                end if;
            end if;
        end if;
    end process;

    process (count)
    begin
        new_count <= count + 1;
    end process;

    count_out <= std_logic_vector(count);

end architecture behaviour;

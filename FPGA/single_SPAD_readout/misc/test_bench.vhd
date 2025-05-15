library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.MATH_REAL.ALL;

entity test_bench is
end entity;

architecture behaviour of test_bench is

component single_SPAD_readout is
	generic (
		COUNTER_SIZE	: natural := 32; --Number of bits for each individual counter (will have 256 of those). Must be whole number of bytes.
		NUM_CYCLES		: natural := 100 -- Number of clock cycles that photons are counted before passing on the value and starting from zero.
	);
	port (
		-- General connections
		CLK   : in  std_logic;
		--RST : in  std_logic;
		
		-- SPI connections
		SPI_SCLK  : out std_logic  := '0'; -- SPI clock
		SPI_CS_N  : out std_logic_vector(0 downto 0) := "0"; -- SPI chip select, active low
		SPI_MOSI  : out std_logic := '0'; -- SPI serial data from master to slave
		SPI_MISO  : in  std_logic := '0';  -- SPI serial data from slave to master
		 
		-- SPAD connection
		input		: in std_logic
  );
end component;



signal CLK : std_logic := '0'; -- make sure you initialise!

-- SPI connections
signal SPI_SCLK  : std_logic; -- SPI clock
signal SPI_CS_N  : std_logic_vector(0 downto 0); -- SPI chip select, active low
signal SPI_MOSI  : std_logic; -- SPI serial data from master to slave
signal SPI_MISO  : std_logic;  -- SPI serial data from slave to master

-- Simulated input from SPAD
signal input		: std_logic := '0';


begin

reader: single_SPAD_readout
	port map (
		-- General connections
		CLK => CLK,
		--RST : in  std_logic;
		
		-- SPI connections
		SPI_SCLK => SPI_SCLK,
		SPI_CS_N => SPI_CS_N,
		SPI_MOSI => SPI_MOSI,
		SPI_MISO => SPI_MISO,
		 
		-- SPAD connection
		input => input
  );
  
	-- Clock
	CLK <= not CLK after 10 ns;
 end architecture;
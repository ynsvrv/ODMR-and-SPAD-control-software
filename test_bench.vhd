library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.MATH_REAL.ALL;

entity test_bench is
end entity;

architecture behaviour of test_bench is
component Array_readout is
	generic (
		COUNTER_SIZE	: natural := 32; --Number of bits for each individual counter (will have 256 of those)
		NUM_CYCLES	: natural := 100
	);
	port (
		-- General connections
		CLK   : in  std_logic;
		--RST : in  std_logic;
		
		-- SPI connections
		SPI_SCLK  : out std_logic; -- SPI clock
		SPI_CS_N  : out std_logic_vector(0 downto 0); -- SPI chip select, active low
		SPI_MOSI  : out std_logic; -- SPI serial data from master to slave
		SPI_MISO  : in  std_logic;  -- SPI serial data from slave to master
		 
		-- Chip connections
		LOAD			: out std_logic := '0';
		CLEAR			: out std_logic := '0';
		SI_w			: out std_logic := '0';
		SI_d			: out std_logic := '0';
		RST_chip		: out std_logic := '0';
		SOX			: in std_logic_vector(15 downto 0);
		CLK_chip		: out std_logic
  );
end component;

component test_chip is
port (
	LOAD			: in std_logic;
	CLEAR			: in std_logic;
	SI_w			: in std_logic;
	SI_d			: in std_logic;
	RST_chip		: in std_logic;
	SOX			: out std_logic_vector(15 downto 0) := (others => '0');
	CLK_chip		: in std_logic
);
end component;

signal CLK : std_logic := '0'; -- make sure you initialise!

-- SPI connections
signal SPI_SCLK  : std_logic; -- SPI clock
signal SPI_CS_N  : std_logic_vector(0 downto 0); -- SPI chip select, active low
signal SPI_MOSI  : std_logic; -- SPI serial data from master to slave
signal SPI_MISO  : std_logic;  -- SPI serial data from slave to master
 
-- Chip connections
signal LOAD			: std_logic := '0';
signal CLEAR			: std_logic := '0';
signal SI_w			: std_logic := '0';
signal SI_d			: std_logic := '0';
signal RST_chip		: std_logic := '0';
signal SOX			: std_logic_vector(15 downto 0) := (others => '0');
signal CLK_chip		: std_logic := '0';

begin
reader: Array_readout
	port map (
		-- General connections
		CLK => CLK,
		--RST : in  std_logic;
		
		-- SPI connections
		SPI_SCLK => SPI_SCLK,
		SPI_CS_N => SPI_CS_N,
		SPI_MOSI => SPI_MOSI,
		SPI_MISO => SPI_MISO,
		 
		-- Chip connections
		LOAD => LOAD,
		CLEAR => CLEAR,
		SI_w => SI_w,
		SI_d => SI_d,
		RST_chip => RST_chip,
		SOX => SOX,
		CLK_chip => CLK_chip
  );
  
 virtual_chip: test_chip
	port map (
		LOAD => LOAD,
		CLEAR => CLEAR,
		SI_w => SI_w,
		SI_d => SI_d,
		RST_chip => RST_chip,
		SOX => SOX,
		CLK_chip => CLK_chip
	);
	
	clk <= not clk after 10 ns;
end architecture;

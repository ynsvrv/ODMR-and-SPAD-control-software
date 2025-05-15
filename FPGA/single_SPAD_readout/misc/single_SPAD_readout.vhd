library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.MATH_REAL.ALL;

entity single_SPAD_readout is
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
end single_SPAD_readout;

architecture behaviour of single_SPAD_readout is

signal RST				: std_logic := '0';
signal RST_counters	: std_logic := '0';
signal DATA_READY		: std_logic := '0';
signal data_counts	: std_logic_vector(COUNTER_SIZE-1 downto 0) := (others => '0');

-- SPI-related internal connections
signal DOUT			: std_logic_vector(7 downto 0);
signal DOUT_VLD	: std_logic;
signal DIN      	: std_logic_vector(7 downto 0);
--signal DIN_ADDR 	: std_logic_vector(0 downto 0) := (others => '0');  -- SPI slave address;
signal DIN_LAST 	: std_logic;
signal DIN_VLD  	: std_logic;
signal DIN_RDY  	: std_logic;


component controller is
	generic (
		NUM_CYCLES							: natural -- Number of readout cycles to be done before sending data to PC.
	);
	port (
		-- General
		CLK           : in  std_logic;
		RST           : in  std_logic;
		
		-- Internal communication between modules
		RST_counters	: out std_logic := '0';
		DATA_READY		: out std_logic := '0'
	);
end component;

component counter is
	generic (
		COUNTER_SIZE	: natural --Number of bits for each individual counter
	);
	port (
		clk          	: in  std_logic;
      reset        	: in  std_logic;
      input 			: in  std_logic;
		counts_out		: out std_logic_vector(COUNTER_SIZE-1 downto 0) := (others => '0')
	);
end component;

component SPI_buffer_sender is
	generic (
		COUNTER_SIZE	: natural --Number of bits for each individual counter
	);
   port (
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
end component;

component SPI_MASTER is
    Generic (
        CLK_FREQ    : natural := 50e6; -- set system clock frequency in Hz
        SCLK_FREQ   : natural := 5e4;  -- set SPI clock frequency in Hz (condition: SCLK_FREQ <= CLK_FREQ/10)
        WORD_SIZE   : natural := 8;    -- size of transfer word in bits, must be power of two
        SLAVE_COUNT : natural := 1     -- count of SPI slaves
    );
    Port (
        CLK      : in  std_logic; -- system clock
        RST      : in  std_logic; -- high active synchronous reset
        -- SPI MASTER INTERFACE
        SCLK     : out std_logic; -- SPI clock
        CS_N     : out std_logic_vector(SLAVE_COUNT-1 downto 0); -- SPI chip select, active in low
        MOSI     : out std_logic; -- SPI serial data from master to slave
        MISO     : in  std_logic; -- SPI serial data from slave to master
        -- INPUT USER INTERFACE
        DIN      : in  std_logic_vector(WORD_SIZE-1 downto 0); -- data for transmission to SPI slave
        --DIN_ADDR : in  std_logic_vector(natural(ceil(log2(real(SLAVE_COUNT))))-1 downto 0); -- SPI slave address
        DIN_LAST : in  std_logic; -- when DIN_LAST = 1, last data word, after transmit will be asserted CS_N
        DIN_VLD  : in  std_logic; -- when DIN_VLD = 1, data for transmission are valid
        DIN_RDY  : out std_logic; -- when DIN_RDY = 1, SPI master is ready to accept valid data for transmission
        -- OUTPUT USER INTERFACE
        DOUT     : out std_logic_vector(WORD_SIZE-1 downto 0); -- received data from SPI slave
        DOUT_VLD : out std_logic  -- when DOUT_VLD = 1, received data are valid
    );
end component;



begin

	CTR: controller
		generic map (
			NUM_CYCLES => NUM_CYCLES
		)
		port map (
			-- General
			CLK => CLK,
			RST => RST,
			
			-- Internal communication between modules
			RST_counters => RST_counters,
			DATA_READY => DATA_READY
		);
		
	CNT: counter
		generic map (
			COUNTER_SIZE => COUNTER_SIZE
		)
		port map (
			clk => CLK,
			reset => RST,
			input => input,
			counts_out => data_counts
		);
	
	SENDER: SPI_Buffer_sender
		generic map (
			COUNTER_SIZE => COUNTER_SIZE
		)
		port map (
			CLK => CLK,
			RST => RST,
			START_TRANSFER => DATA_READY,
			DATA_IN => data_counts,
			  
			-- Connections with SPI Master module
			DIN => DIN,
			DIN_LAST => DIN_LAST,
			DIN_VLD  => DIN_VLD,
			DIN_RDY => DIN_RDY
		);
		
	SPI_MAMA: SPI_MASTER
		generic map (
			SCLK_FREQ => 5e4
		)
		port map (
			CLK => CLK,
			RST => RST,
			SCLK => SPI_SCLK,
			CS_N => SPI_CS_N,
			MOSI => SPI_MOSI,
			MISO => SPI_MISO,
			DIN => DIN,
			--DIN_ADDR => ,
			DIN_LAST => DIN_LAST,
			DIN_VLD => DIN_VLD,
			DIN_RDY => DIN_RDY,
			DOUT => DOUT,
			DOUT_VLD => DOUT_VLD
		);

end architecture;
library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.MATH_REAL.ALL;
use IEEE.NUMERIC_STD.ALL;

entity Array_readout is
	generic (
		COUNTER_SIZE	: natural := 32; --Number of bits for each individual counter (will have 256 of those). Must be whole number of bytes.
		NUM_CYCLES		: natural := 100
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
		 
		-- Chip connections
		LOAD			: out std_logic := '0';
		CLEAR			: out std_logic := '0';
		SI_w			: out std_logic := '0';
		SI_d			: out std_logic := '0';
		RST_chip		: out std_logic := '0';
		SOX			: in std_logic_vector(15 downto 0);
		CLK_chip		: out std_logic
  );
end Array_readout;

architecture behaviour of Array_readout is
	-- Clock signals
	signal clk_slow  	: std_logic;
	signal clk_slow_counter	: natural := 0;

	signal RST				: std_logic;
	signal RST_counters	: std_logic;
	signal DATA_READY		: std_logic;
	signal data_counts	: std_logic_vector(COUNTER_SIZE*256-1 downto 0);
	--signal command			: natural;
	signal start			: std_logic;
	signal initial_reset_done	: std_logic := '0';
	
	-- SPI-related internal connections
	signal DOUT			: std_logic_vector(7 downto 0);
	signal DOUT_VLD	: std_logic;
	signal DIN      	: std_logic_vector(7 downto 0);
   --signal DIN_ADDR 	: std_logic_vector(0 downto 0) := (others => '0');  -- SPI slave address;
   signal DIN_LAST 	: std_logic;
   signal DIN_VLD  	: std_logic;
   signal DIN_RDY  	: std_logic;
	--signal sender_request : unsigned(8 downto 0);
	--signal sender_byte	 : std_logic_vector(7 downto 0);
	
	signal load_internal	: std_logic;
	
	constant num_bytes	: natural := COUNTER_SIZE*256/8; -- Number of bytes in the data buffer

	component serial_counter is
		generic (
			COUNTER_SIZE	: natural --Number of bits for each individual counter
		);
		port (
			clk          	: in  std_logic;
			reset        	: in  std_logic;
			serial_input 	: in  std_logic;
			load				: in	std_logic;
			counts_out		: out std_logic_vector(COUNTER_SIZE*16-1 downto 0)
		);
	end component;

	component controller is
		Generic (
			NUM_CYCLES	: natural -- Number of readout cycles to be done before sending data to PC.
		);
		port (
			-- General
			CLK           : in  std_logic;
			RST           : in  std_logic;
			
			-- Internal communication between modules
			--command			: in natural := 0;
			--start				: in std_logic := '0';
			RST_counters	: out std_logic := '0';
			DATA_READY		: out std_logic := '0';

			-- Chip signals
			LOAD			: out std_logic := '0';
			CLEAR			: out std_logic := '0';
			SI_w			: out std_logic := '0';
			SI_d			: out std_logic := '0';
			RST_chip		: out std_logic := '0'
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
		DATA_IN    			: in  std_logic_vector(COUNTER_SIZE*256-1 downto 0); -- Data to transfer
		  
		-- Connections with SPI Master module
		DIN      : out  std_logic_vector(7 downto 0) := (others => '0'); -- data for transmission to SPI slave
      --DIN_ADDR : out  std_logic_vector(0 downto 0) := (others => '0');  -- SPI slave address
      DIN_LAST : out  std_logic := '0'; -- when DIN_LAST = 1, last data word, after transmit will be asserted CS_N
      DIN_VLD  : out  std_logic := '0'; -- when DIN_VLD = 1, data for transmission are valid
      DIN_RDY  : in std_logic -- when DIN_RDY = 1, SPI master is ready to accept valid data for transmission
	);
	end component;
	
--	component command_resciever is
--		port (
--			CLK			: in std_logic;
--			RST			: in std_logic;
--			DOUT			: in std_logic_vector(7 downto 0); -- From SPI master
--			DOUT_VLD		: in std_logic; -- From SPI master
--			command_out	: out natural := 0; -- Connect with controller
--			start			: out std_logic := '0' -- Tells the controller to start measuring
--		);
--	end component;
	
	component SPI_MASTER is
    Generic (
        CLK_FREQ    : natural := 1e6; -- set system clock frequency in Hz
        SCLK_FREQ   : natural := 5e6;  -- set SPI clock frequency in Hz (condition: SCLK_FREQ <= CLK_FREQ/10)
        WORD_SIZE   : natural := 8    -- size of transfer word in bits, must be power of two
        --SLAVE_COUNT : natural := 1     -- count of SPI slaves
    );
    Port (
        CLK      : in  std_logic; -- system clock
        RST      : in  std_logic; -- high active synchronous reset
        -- SPI MASTER INTERFACE
        SCLK     : out std_logic; -- SPI clock
        --CS_N     : out std_logic_vector(SLAVE_COUNT-1 downto 0); -- SPI chip select, active in low
		  CS_N	  : out std_logic_vector(0 downto 0);
        MOSI     : out std_logic; -- SPI serial data from master to slave
        MISO     : in  std_logic; -- SPI serial data from slave to master
        -- INPUT USER INTERFACE
        DIN      : in  std_logic_vector(WORD_SIZE-1 downto 0); -- data for transmission to SPI slave
        --DIN_ADDR : in  std_logic_vector(0 downto 0); -- SPI slave address
        DIN_LAST : in  std_logic; -- when DIN_LAST = 1, last data word, after transmit will be asserted CS_N
        DIN_VLD  : in  std_logic; -- when DIN_VLD = 1, data for transmission are valid
        DIN_RDY  : out std_logic; -- when DIN_RDY = 1, SPI master is ready to accept valid data for transmission
        -- OUTPUT USER INTERFACE
        DOUT     : out std_logic_vector(WORD_SIZE-1 downto 0); -- received data from SPI slave
        DOUT_VLD : out std_logic  -- when DOUT_VLD = 1, received data are valid
    );
	end component;

begin

	gen: for i in 0 to 15 generate
		uut: serial_counter
		generic map (
			COUNTER_SIZE => COUNTER_SIZE  -- Pass the generic from serial_counter to input_counter
		)
		port map (
			clk => clk_slow,
			reset => RST_counters,
			serial_input => SOX(i),
			load => load_internal,
			counts_out => data_counts( (i+1)*(16*COUNTER_SIZE) - 1 downto i*(16*COUNTER_SIZE) )
		);
	end generate;
	
	CTR: controller
		generic map (
			NUM_CYCLES => NUM_CYCLES
		)
		port map (
				-- General
			CLK => clk_slow,
			RST => RST,
			
			-- Internal communication between modules
			--command => command,
			--start => start,
			RST_counters => RST_counters,
			DATA_READY => DATA_READY,

			-- Chip signals
			LOAD => load_internal,
			CLEAR => CLEAR,
			SI_w => SI_w,
			SI_d => SI_d,
			RST_chip => RST_chip
		);
		
	SENDER: SPI_buffer_sender
		generic map (
			COUNTER_SIZE => COUNTER_SIZE  -- Pass the generic from serial_counter to input_counter
		)
		port map (
			CLK => clk_slow,
			RST => RST,
			START_TRANSFER => DATA_READY,
			DATA_IN => data_counts,
			DIN => DIN,
			--DIN_ADDR => DIN_ADDR,
			DIN_LAST => DIN_LAST,
			DIN_VLD => DIN_VLD,
			DIN_RDY => DIN_RDY
		);
		
--	RESCIEVER: command_resciever
--		port map (
--			CLK => CLK,
--			RST => RST,
--			DOUT => DOUT,
--			DOUT_VLD => DOUT_VLD,
--			command_out => command,
--			start => start
--		);
		
	SPI_MAMA: SPI_MASTER
		generic map (
			SCLK_FREQ => 5e4
		)
		port map (
			CLK => clk_slow,
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

-- Manage the slower clock
process(CLK)
begin
  if(rising_edge(CLK)) then
    clk_slow_counter <= clk_slow_counter + 1;
    if(clk_slow_counter < 25) then
      clk_slow <= '1';
    else
      clk_slow <= '0';
    end if;
	 if clk_slow_counter = 49 then
		clk_slow_counter <= 0;
	 end if;
  end if;
end process;

process(clk_slow)
begin
	if(rising_edge(clk_slow)) then
		-- Send reset pulse at initialization to make sure all modules are completely initialized
		if(initial_reset_done = '0') then
			RST <= '1';
			initial_reset_done <= '1';
		else
			RST <= '0';
		end if;
		
	end if;
end process;

-- Forward clock to chip
CLK_chip <= clk_slow;

-- Forward internal load signal to chip
LOAD <= load_internal;

end architecture behaviour;

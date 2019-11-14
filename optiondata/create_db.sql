-- Table structure for table fullday
--

DROP TABLE IF EXISTS fullday;
CREATE TABLE fullday (
    id integer NOT NULL,
    underlying_symbol character varying(10) DEFAULT NULL::character varying,
    quote_date date,
    root character varying(10) DEFAULT NULL::character varying,
    expiration date,
    strike numeric(10,4) DEFAULT NULL::numeric,
    option_type character(1) DEFAULT NULL::bpchar,
    open numeric(10,4) DEFAULT NULL::numeric,
    high numeric(10,4) DEFAULT NULL::numeric,
    low numeric(10,4) DEFAULT NULL::numeric,
    close numeric(10,4) DEFAULT NULL::numeric,
    trade_volume integer,
    bid_size_1545 integer,
    bid_1545 numeric(20,4) DEFAULT NULL::numeric,
    ask_size_1545 integer,
    ask_1545 numeric(20,4) DEFAULT NULL::numeric,
    underlying_bid_1545 numeric(10,4) DEFAULT NULL::numeric,
    underlying_ask_1545 numeric(10,4) DEFAULT NULL::numeric,
    bid_size_eod integer,
    bid_eod numeric(20,4) DEFAULT NULL::numeric,
    ask_size_eod integer,
    ask_eod numeric(20,4) DEFAULT NULL::numeric,
    underlying_bid_eod numeric(10,4) DEFAULT NULL::numeric,
    underlying_ask_eod numeric(10,4) DEFAULT NULL::numeric,
    vwap text,
    open_interest integer,
    delivery_code character varying(100) DEFAULT NULL::character varying
);


--
-- Table structure for table optiondata
--

DROP TABLE IF EXISTS optiondata;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE optiondata (
  underlying_symbol varchar(10) DEFAULT NULL,
  quote_date date DEFAULT NULL,
  root varchar(10) DEFAULT NULL,
  expiration date DEFAULT NULL,
  strike decimal(10,4) DEFAULT NULL,
  option_type char(1) DEFAULT NULL,
  open decimal(10,4) DEFAULT NULL,
  high decimal(10,4) DEFAULT NULL,
  low decimal(10,4) DEFAULT NULL,
  close decimal(10,4) DEFAULT NULL,
  trade_volume integer DEFAULT NULL,
  bid_size_1545 integer DEFAULT NULL,
  bid_1545 decimal(20,4) DEFAULT NULL,
  ask_size_1545 integer DEFAULT NULL,
  ask_1545 decimal(10,4) DEFAULT NULL,
  underlying_bid_1545 decimal(10,4) DEFAULT NULL,
  underlying_ask_1545 decimal(10,4) DEFAULT NULL,
  bid_size_eod integer DEFAULT NULL,
  bid_eod decimal(20,4) DEFAULT NULL,
  ask_size_eod integer DEFAULT NULL,
  ask_eod decimal(20,4) DEFAULT NULL,
  underlying_bid_eod decimal(10,4) DEFAULT NULL,
  underlying_ask_eod decimal(10,4) DEFAULT NULL,
  vwap text,
  open_interest integer DEFAULT NULL,
  delivery_code varchar(100) DEFAULT NULL,
  id SERIAL PRIMARY KEY NOT NULL,
  iv decimal(65,30) DEFAULT NULL,
  delta decimal(65,30) DEFAULT NULL,
  theta decimal(65,30) DEFAULT NULL,
  vega decimal(65,30) DEFAULT NULL,
  mid_1545 decimal(20,4) DEFAULT NULL,
  underlying_mid_1545 decimal(20,4) DEFAULT NULL
); 


CREATE INDEX idx_ask_1545 ON fullday USING btree (ask_1545);
CREATE INDEX idx_bid_1545 ON fullday USING btree (bid_1545);
CREATE INDEX idx_fullday_expiration ON fullday USING btree (expiration);
CREATE INDEX idx_option_type ON fullday USING btree (option_type);
CREATE INDEX idx_quote_date ON fullday USING btree (quote_date);
CREATE INDEX idx_strike ON fullday USING btree (strike);
CREATE INDEX idx_underlying_symbol ON fullday USING btree (underlying_symbol);


CREATE INDEX idx_date ON optiondata USING btree (quote_date);
CREATE INDEX idx_expiration ON optiondata USING btree (expiration);
CREATE INDEX idx_iv ON optiondata USING btree (iv);
CREATE INDEX idx_mid_1545 ON optiondata USING btree (mid_1545);
CREATE INDEX idx_type ON optiondata USING btree (option_type);
CREATE INDEX idx_underlying ON optiondata USING btree (underlying_symbol);

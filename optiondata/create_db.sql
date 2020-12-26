--
-- Table structure for table optiondata
--

DROP TABLE IF EXISTS optiondata;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE optiondata (
  id SERIAL PRIMARY KEY NOT NULL,
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
  vwap decimal DEFAULT NULL,
  open_interest integer DEFAULT NULL,
  delivery_code varchar(100) DEFAULT NULL,
  iv decimal(65,30) DEFAULT NULL,
  delta decimal(65,30) DEFAULT NULL,
  theta decimal(65,30) DEFAULT NULL,
  vega decimal(65,30) DEFAULT NULL,
  mid_1545 decimal(20,4) DEFAULT NULL,
  underlying_mid_1545 decimal(20,4) DEFAULT NULL
); 

CREATE INDEX idx_date ON optiondata USING btree (quote_date);
CREATE INDEX idx_expiration ON optiondata USING btree (expiration);
CREATE INDEX idx_iv ON optiondata USING btree (iv);
CREATE INDEX idx_mid_1545 ON optiondata USING btree (mid_1545);
CREATE INDEX idx_type ON optiondata USING btree (option_type);
CREATE INDEX idx_underlying ON optiondata USING btree (underlying_symbol);

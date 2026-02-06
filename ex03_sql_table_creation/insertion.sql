
-- Vendeurs
INSERT INTO dim_vendor (vendor_id, vendor_name) VALUES
(1, 'Creative Mobile Technologies, LLC'),
(2, 'Curb Mobility, LLC'),
(5, 'Uber'),
(6, 'Myle Technologies Inc'),
(7, 'Helix');

-- Types de Paiement
INSERT INTO dim_payment_type (payment_type_id, payment_name) VALUES
(0, 'Flex Fare trip'),
(1, 'Credit card'),
(2, 'Cash'),
(3, 'No charge'),
(4, 'Dispute'),
(5, 'Unknown'),
(6, 'Voided trip');

-- Codes Tarifs
INSERT INTO dim_rate_code (rate_code_id, rate_description) VALUES
(1, 'Standard rate'),
(2, 'JFK'),
(3, 'Newark'),
(4, 'Nassau or Westchester'),
(5, 'Negotiated fare'),
(6, 'Group ride'),
(99, 'Null/unknown');


-- Localisations 
COPY dim_location(location_id, borough, zone, service_zone)
FROM '/tmp/taxi_zone_lookup.csv'
DELIMITER ','
CSV HEADER;

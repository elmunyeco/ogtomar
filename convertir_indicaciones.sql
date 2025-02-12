ALTER TABLE indicaciones MODIFY COLUMN eliminado TINYINT(1);

UPDATE indicaciones 
SET eliminado = CASE      
	WHEN eliminado = b'0' THEN 0      
	ELSE 1  
END;

ALTER TABLE indicaciones CHANGE idHC historia_clinica_id bigint(20) NOT NULL;

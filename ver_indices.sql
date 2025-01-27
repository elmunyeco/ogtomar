SELECT 
    TABLE_SCHEMA AS BaseDeDatos,
    TABLE_NAME AS Tabla,
    INDEX_NAME AS Indice,
    COLUMN_NAME AS Columna,
    NON_UNIQUE AS Es_Unico,
    INDEX_TYPE AS Tipo_Indice
FROM 
    information_schema.STATISTICS
WHERE 
    TABLE_SCHEMA = 'cardioprieto'
ORDER BY 
    TABLE_NAME, INDEX_NAME;


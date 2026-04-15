# QA bundle

## Contenido
- `cardioprieto_schema.sql`
- `cardioprieto_data.sql`
- `auth_dump.sql`
- `restore_qa.sh`
- `QA_DUMP_README.md`

## Uso rapido (en QA)

```bash
./restore_qa.sh
```

Si el contenedor no se llama `nuevo_cardioprieto`:

```bash
DB_CONTAINER=OTRO ./restore_qa.sh
```

Si el password es distinto:

```bash
DB_PASS=OTRO ./restore_qa.sh
```

# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }

# CELL ********************

# Exemplo básico em PySpark (Batch)
df = spark.read.format("csv").load("Files")

#aqui aplicaria tranformações

# Salvar como Tabela Delta no Lakehouse
df_transformado.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable("tabela_destinataria")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

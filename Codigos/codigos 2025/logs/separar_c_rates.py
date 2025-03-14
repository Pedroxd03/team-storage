import pandas as pd
import os

script_folder = os.path.dirname(__file__)

# Cargar el archivo CSV en un DataFrame
csv_file = script_folder + '/processed/datos_descarga_resampled.csv'
df = pd.read_csv(csv_file)

# Verificar si el DataFrame original tiene datos
print("Número de filas y columnas en el DataFrame original:", df.shape)

# Obtener las columnas que contienen "C_rate" y son numéricas
def is_numeric_column(column):
    try:
        pd.to_numeric(column)
        return True
    except ValueError:
        return False

crate_columns = [col for col in df.columns if 'C_rate' in col and is_numeric_column(df[col])]

# Dividir el DataFrame en subconjuntos según el valor de "C_rate"
dfs_by_crate = {crate: df[df[crate].round(1) == df[crate]] for crate in crate_columns}

# Imprimir información sobre cada subconjunto
for crate, sub_df in dfs_by_crate.items():
    print(f"Subconjunto para C_rate={crate}: Número de filas: {sub_df.shape[0]}")

    # Guardar cada subconjunto en un archivo CSV separado
    output_file = f'crate_{crate}.csv'
    sub_df.to_csv(script_folder + "/processed/" + output_file, index=False)

print("Archivos CSV creados exitosamente.")

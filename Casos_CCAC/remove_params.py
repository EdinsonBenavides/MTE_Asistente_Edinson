import json

# Ruta al archivo JSON
ruta_archivo = 'config.json'

# Nuevo valor que deseas asignar a key_pass
nuevo_valor = ''

# parametros a modificar

list_params = ["private_key", "broker", "userMQTT", "passwordMQTT", "account_address"]
# Leer el contenido del archivo JSON
with open(ruta_archivo, 'r') as archivo:
    datos = json.load(archivo)

# Modificar el valor de key_pass si existe
for data in list_params:
    if data in datos:
        datos[data] = nuevo_valor
        print(f"Se actualizó {data} a: {nuevo_valor}")
    else:
        print("La clave 'key_pass' no existe en el JSON. Se añadirá.")
        datos['key_pass'] = nuevo_valor

# Guardar los cambios en el archivo
with open(ruta_archivo, 'w') as archivo:
    json.dump(datos, archivo, indent=4)

print("Archivo actualizado correctamente.")

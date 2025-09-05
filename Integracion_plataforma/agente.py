import json
import os
from dotenv import load_dotenv
import time
import requests
import paho.mqtt.client as mqtt
import json
import queue
import threading


## urls para hacer uso de los metodos ##
urls = {"autentication": "http://10.10.10.76:3601/api_authentication/",
        "get_blocks": "http://10.10.10.76:3601/get_blocks/",
        "demand_energy": "http://10.10.10.76:3601/demand_energy/",
        "add_tokens":"http://10.10.10.76:3601/add_tokens/",
        "make_transaction": "http://10.10.10.76:3601/make_transaction/",
        "get_org_values":"http://10.10.10.76:3601/get_org_values/"}

credentials = {
    "email": "edinson@mte.com",
    "password": "edinson123"
    }

owner_ID = 1233193288 # ID del usuario propietario


def login(credentials, url = urls["autentication"]):
    #metodo para hacer login y obtener el token
    
    # A GET request to the API
    response = requests.post(url, json=credentials)

    # Print the response
    response_json = response.json()

    return response_json["token"]

def make_transaction_energy(id_user, id_user2,energy):
    #metodo para hacer una transaccion de energia entre dos usuarios
    #id_user es el usuario que envia la energia y id_user2 es el usuario que recibe
    #energy es la cantidad de energia que se envia 

    token = login(credentials, url = urls["autentication"])

    json_data = {
        "id_user": id_user,
        "id_user2": id_user2,
        "energy": energy,
        "money": 0,
        "token": token
    } 
    
    # A GET request to the API
    response = requests.post(urls["make_transaction"], json=json_data)

    # Print the response
    response_json = response.json()
    print(response_json)

def make_transaction_price(id_user, id_user2,money,token):
    #metodo para hacer una transaccion de dinero entre dos usuarios
    #id_user es el usuario que envia la energia y id_user2 es el usuario que recibe
    #money es la cantidad de dinero que se envia

    json_data = {
        "id_user": id_user,
        "id_user2": id_user2,
        "energy": 0,
        "money": money,
        "token": token
    } 
    
    # A GET request to the API
    response = requests.post(urls["make_transaction"], json=json_data)

    # Print the response
    response_json = response.json()
    print(response_json)

# Leer el archivo JSON de configuración 
with open('config.json', 'r') as file:
    info_config = json.load(file)

# Configuración del broker
broker = info_config['broker']
port = info_config['port']
topics_public = info_config['topics_public']
topic_suscrib = info_config['topic_suscriptor']
ID_agente = info_config['ID_agente']
admin = info_config['admin']
state_optimizacion = True
comprador = info_config['comprador']
address = info_config['address']

# Crear cola
Q  = queue.Queue()

def make_transaction(cantidad_potencia,precio, vendedor):
    
    token = login(credentials, url = urls["autentication"])
    
    vendedor_ID = vendedor

    pago = round(cantidad_potencia*precio)  # Valor numérico en Wei

    make_transaction_price(owner_ID, vendedor_ID,pago,token)
    

def all_transactions(data):
    # Leer el archivo JSON de configuración 
    with open('config.json', 'r') as file:
        info_config = json.load(file)


    comprador = info_config['comprador']

    if comprador:
        optimos = data["resultado"]
        keys_resultado = data["resultado"].keys()
        for i in keys_resultado:
            make_transaction(optimos[i],data["precio"],address[i])

# Función de publicación
def publish(data,topic, broker):
    global publish_flag
    # Convertir el diccionario a una cadena JSON
    message_str = json.dumps(data)

    # Crear una instancia del cliente
    client = mqtt.Client()

    try:
        # Conectarse al broker
        client.connect(broker, port, 60)
        if publish_flag:
            # Publicar el mensaje
            client.publish(topic, message_str)
            print(f"Mensaje JSON publicado en {topic}: {message_str}")
            time.sleep(1)  # Esperar 5 segundos antes de publicar nuevamente
    except Exception as e:
        print(f"Error al conectar o publicar: {e}")
    finally:
        # Desconectarse del broker
        client.disconnect()
        print("Cliente MQTT desconectado")


# Función de suscripción
def subscribe(topic,broker):
    # Función callback cuando se recibe un mensaje
    global global_data
    def on_message(client, userdata, message):
        try:
            # Convertir el payload a un diccionario
            data = json.loads(message.payload.decode())
            print(f"Mensaje recibido en {message.topic}: {data}")
            
            transactions = threading.Thread(target=all_transactions,args=(data,))
            transactions.start()

        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")

    # Crear una instancia del cliente
    client = mqtt.Client()

    try:
        # Asignar la función callback
        client.on_message = on_message
        # Conectarse al broker
        client.connect(broker, port, 60)
        # Suscribirse al tema
        client.subscribe(topic)
        print(f"suscrito a: {topic}")
        # Mantenerse en escucha
        client.loop_forever()
    except Exception as e:
        print(f"Error al conectar o suscribir: {e}")

# Crear hilos para publicar y suscribir
subscribe_thread = threading.Thread(target=subscribe,args=(topic_suscrib,broker))


# Iniciar hilos
subscribe_thread.start()



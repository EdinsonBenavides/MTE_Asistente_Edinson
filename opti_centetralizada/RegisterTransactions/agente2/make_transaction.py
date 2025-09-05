import json
import os
from web3 import Web3
from dotenv import load_dotenv
import time
import requests
import paho.mqtt.client as mqtt
import json
import queue
import threading

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
    # Traemos información del contrato
    try:
        with open('Register_transaction.json', 'r') as file:
            data_contract = json.load(file)
            # Traemos el ABI
            abiContract = data_contract["abi"]
            # Dirección del Contrato
            addressContract = data_contract["adress_contract"]
            # Nodo de Alchemy donde esta desplegado el contrato
            Nodo_Alchemy = data_contract["Nodo_Alchemy"]
    except json.JSONDecodeError as e:
        print(f"Error al leer información del contrato JSON: {e}")

    w3 = Web3(Web3.HTTPProvider(Nodo_Alchemy))

    # Cargar las variables del archivo .env
    load_dotenv()

    # Instanciamos la direccion de la cuenta (llave publica)
    comprador_account = os.getenv('Public_Key')
    # Instanciamos la llave privada
    private_key = os.getenv('Private_Key')

    # La cuenta del vendedor (a la que se enviará el dinero).
    vendedor_address = vendedor

    # Verificamos si la conexión es exitosa
    if not w3.is_connected():
        print("Error: No se pudo conectar al nodo de Ethereum. Asegúrate de que Ganache o tu nodo estén corriendo.")
        exit()
    else:
        print("Conexión exitosa a la red de Ethereum.")


    # Creamos una instancia del contrato
    contract = w3.eth.contract(address=addressContract, abi=abiContract)

    # 3. Datos de la transacción

    

    pago_en_wei = round(cantidad_potencia*precio)  # Valor numérico en Wei

    # 4. Construcción y envío de la transacción
    
    try:

        tx = contract.functions.comprarEnergia(vendedor_address, cantidad_potencia).build_transaction({
            'from': comprador_account,
            'value': pago_en_wei,  # Se usa directamente el valor en Wei
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(comprador_account),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print("Transacción enviada con hash:", tx_hash.hex())
        print("Esperando que la transacción se mine...")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # 5. Verificación y resultados
        if receipt.status == 1:
            print("¡Transacción exitosa!")
            print("Bloque de la transacción:", receipt.blockNumber)
            print("Gas usado:", receipt.gasUsed)
    except Exception as e:
        print(f"Ocurrió un error: {e}")

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



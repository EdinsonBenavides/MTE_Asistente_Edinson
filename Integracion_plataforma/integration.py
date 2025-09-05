import time
import requests
import paho.mqtt.client as mqtt
import json
import threading
import queue
""" El esquema esta realizado para que el agente central realice la optimizacion 
y tambien realice el pago de la energia comprada a cada agente contribuidor.
Para el pago se tiene en cuenta un valor de potencia unitario"""

## urls para hacer uso de los metodos ##
urls = {"autentication": "http://10.10.10.76:3601/api_authentication/",
        "get_blocks": "http://10.10.10.76:3601/get_blocks/",
        "demand_energy": "http://10.10.10.76:3601/demand_energy/",
        "add_tokens":"http://10.10.10.76:3601/add_tokens/",
        "make_transaction": "http://10.10.10.76:3601/make_transaction/",
        "get_org_values":"http://10.10.10.76:3601/get_org_values/"}

credentials = {
    "email": "",
    "password": ""
    }

owner_ID =  # ID del usuario propietario


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
    
def get_params_org(n_agentes):
    a = [0]*n_agentes
    b = [0]*n_agentes
    c = [0]*n_agentes
    up_lim = [0]*n_agentes
    down_lim = [0]*n_agentes
    
    token = login(credentials, url = urls["autentication"])
    for i in range(n_agentes):
        json_data = {
          "id_organization": i + 1,
          "token": token
        }
        # A GET request to the API
        response = requests.post(urls["get_org_values"], json=json_data)
        
        # Print the response
        response_json = response.json()[0]
        

        a[i] = response_json["cost_a"]/100
        b[i] = response_json["cost_b"]/100
        c[i] = response_json["cost_c"]/100
        up_lim[i] = response_json["min_gen_limit"]
        down_lim[i] = response_json["max_gen_limit"]
        
    return a,b,c,up_lim,down_lim

###################################################
########### MQTT Section ##########################
###################################################

# Crear cola
Q  = queue.Queue()

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

# Configuración admin
global_data = {}
state_optimizacion = info_config['state_optimizacion']

publicadores = topics_public.keys()
lastet_data = {publicador:0 for publicador in publicadores} 

global_data = lastet_data.copy()
publish_flag = True
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
            
            global_data[data['publicador']] = data["potencia"]
            Q.put(global_data)

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

def writerJsonData():
    global state_optimizacion

    while True:
        if state_optimizacion:
            data = Q.get()
            with open('data_optimización.json', 'w') as file:
                json.dump(data, file)

# Crear hilos para publicar y suscribir
#publish_thread = threading.Thread(target=publish)
#subscribe_thread = threading.Thread(target=subscribe,args=(topic_suscrib,broker))


# Iniciar hilos
#publish_thread.start()
#subscribe_thread.start()

###############################################
################# Optimizacion ################
###############################################

def f_i(b,c,p):

    fi = -(b + 2*(c*p))  + 3e3
    return fi

def X_k(fi,sumX,f_mean,x_gorr,p):
    alpha = 1e-15
    x_k =  p + alpha*(x_gorr)*(fi*sumX - f_mean)

    return x_k


#### Lectura de parametros

P_d = 1150
numAgentes = 5

a,b,c,up_limits,down_limits = get_params_org(numAgentes)

x0 = ([350, 300, 250, 200, 50])


### Inicialización de iteracion 0
x_gorr_k = ([0]*numAgentes)
fi_k = ([0]*numAgentes)
P_k = x0.copy()

for i in range(numAgentes):
    x_gorr_k[i] = x0[i]*(up_limits[i] - x0[i])*(x0[i] - down_limits[i])
    fi_k[i] = f_i(b[i],c[i],x0[i])

sumX = sum(x_gorr_k)
f_mean = sum(([fi_k[i]*x_gorr_k[i] for i in range(numAgentes)]))

#### Iteraciones para optimización
for k in range(1000):
    for i in range(numAgentes):
        P_k[i] = X_k(fi_k[i],sumX,f_mean,x_gorr_k[i],P_k[i])
    
    for i in range(numAgentes):
        x_gorr_k[i] = P_k[i]*(up_limits[i] - P_k[i])*(P_k[i] - down_limits[i])
        fi_k[i] = f_i(b[i],c[i],P_k[i])
    sumX = sum(x_gorr_k)
    f_mean = sum(([fi_k[i]*x_gorr_k[i] for i in range(numAgentes)]))

print(P_k)

###############################################################################
############### Pago de potencia a cada agente ################################
###############################################################################

#### Envio de valores a los agentes 

for i in range(numAgentes):
    global_data[str(i+1)] = P_k[i]

data = {"publicador": "admin",
 "state_optimizacion": state_optimizacion, 
 "potencia_demandada": P_d, 
 "numero_de_agentes": 6, 
 "num_iteraciones":1000, 
 "data":global_data
}
for publicador in publicadores:
        publish(data,topics_public[publicador],broker)


################ Pagos a agentes ############################
# Poner ID de cada agente en la lista, segun corresponda
IDs_agentes = [1093458050, 1233193101, 1233193102, 1233193103, 1233193104] 

# Se define el precio por unidad de KW
price_unit_kW = 100

# Pago de potencia a cada agente
token = login(credentials, url = urls["autentication"])
for i in range(numAgentes):
    print(price_unit_kW*P_k[i])
    make_transaction_price(owner_ID,IDs_agentes[i],price_unit_kW*P_k[i],token)
    time.sleep(2)

response = requests.post(urls["get_blocks"], json={"token":token})
# Print the response
response_json = response.json()
print(response_json)

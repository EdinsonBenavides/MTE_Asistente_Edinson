import time
import requests
import paho.mqtt.client as mqtt
import json
import threading
import queue
from scipy.optimize import minimize

""" El esquema esta realizado para que el agente central realice la optimizacion 
y tambien realice el pago de la energia comprada a cada agente contribuidor.
Para el pago se tiene en cuenta un valor de potencia unitario"""



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

def Costs_i(P_ij,A,B,D_ij,P_tr,i,S_i,B_j):
    sum_dp_ij = 0
    if i in S_i:
        for j in B_j:
            sum_dp_ij = sum_dp_ij + D_ij[(i,j)]*P_ij[(i,j)]    
    if i in B_j:
        for j in S_i:
            sum_dp_ij = sum_dp_ij - D_ij[(j,i)]*P_ij[(j,i)] 
            
    C_i = A[i]*(P_tr[i]**2) + B[i]*P_tr[i] + (sum_dp_ij)
    return C_i

def ID_P(N):
    index_ij = []
    Buyers = [j for j in range(int(N/2),N)]
    Sellers = [i for i in range(int(N/2))]
    for i in range(int(N/2)):
        for j in range(int(N/2),N):
            if i != j:
                index_ij.append((i,j))
                
    return [index_ij,Sellers,Buyers]

def dicP_ij(P,ij):
    P_ij = {}
    for inx in range(len(P)):
        P_ij[ij[inx]] = P[inx]
    return P_ij

def Sum_Ptr(P_ij,Sellers_i,Buyers_j):
    P_tr_i = []
    for i in Sellers_i:
        sum_ptr = 0
        for j in Buyers_j:
            sum_ptr = sum_ptr + P_ij[(i,j)]
        P_tr_i.append(sum_ptr)
        
    for j in Buyers_j:
        sum_ptr = 0
        for i in Sellers_i:
            sum_ptr = sum_ptr - P_ij[(i,j)]
        P_tr_i.append(sum_ptr)
    
    return P_tr_i

def obj(P):
    a = [0.0031, 0.0074, 0.0066, 0.0063, 0.0069, 0.0095]
    b = [8.71, 3.53, 7.58, 2.24, 8.53, 3.46]
    dij = [0.51, 0.51, 0.72, 0.1, 0.12, 0.04, 0.1, 0.12, 0.04]
    N = 6
    ij,S_i,B_j = ID_P(N)
    D_ij = dicP_ij(dij,ij)
    P_ij = dicP_ij(P,ij)
    P_tr=Sum_Ptr(P_ij,S_i,B_j)
    C = []
    for i in range(N):
        C_i = Costs_i(P_ij,a,b,D_ij,P_tr,i,S_i,B_j)
        C.append(C_i)
            
    return sum(C) 

def Restri(P):
    lb = [-105, -115, -125, 0.01, 0.01, 0.01]
    ub = [-0.01, -0.01, -0.01, 100, 110, 95]
    N = 6
    ij,S_i,B_j = ID_P(N)
    P_ij = dicP_ij(P,ij)
    P_tr=Sum_Ptr(P_ij,S_i,B_j)
    restr = []
    for i in range(N):
        restr.append(P_tr[i] - lb[i])
    for i in range(N):
        restr.append(-P_tr[i] + ub[i])
    restr.append(sum(P_tr))
    return [restr,P_tr]

def Price_i(A,B,D_ij,P_tr,i,S_i,B_j):
    sum_dp_ij = 0
    if i in S_i:
        for j in B_j:
            sum_dp_ij = sum_dp_ij + D_ij[(i,j)]   
    if i in B_j:
        for j in S_i:
            sum_dp_ij = sum_dp_ij + D_ij[(j,i)]
            
    price_i = A[i]*(P_tr[i]) + B[i] + (sum_dp_ij)
    return price_i

def Price_T(P):
    a = [0.0031, 0.0074, 0.0066, 0.0063, 0.0069, 0.0095]
    b = [8.71, 3.53, 7.58, 2.24, 8.53, 3.46]
    dij = [0.51, 0.51, 0.72, 0.1, 0.12, 0.04, 0.1, 0.12, 0.04]
    N = 6
    ij,S_i,B_j = ID_P(N)
    D_ij = dicP_ij(dij,ij)
    P_ij = dicP_ij(P,ij)
    P_tr=Sum_Ptr(P_ij,S_i,B_j)
    price = []
    for i in range(N):
        price_i = Price_i(a,b,D_ij,P_tr,i,S_i,B_j)
        price.append(price_i)
            
    return sum(price)

def Price2():
    N=6
    a = [0.0031, 0.0074, 0.0066, 0.0063, 0.0069, 0.0095]
    b = [8.71, 3.53, 7.58, 2.24, 8.53, 3.46]
    num = 0
    for i in range(N):
        num = num + (b[i]/a[i])
    den = 0
    for i in range(N):
        den = den + (1/a[i])
        
    return num/den

def R1(var):
    vr = Restri(var)[0]
    return vr[-1]
def R2(var):
    vr = Restri(var)[0]
    return vr[0]
def R3(var):
    vr = Restri(var)[0]
    return vr[1]
def R4(var):
    vr = Restri(var)[0]
    return vr[2]
def R5(var):
    vr = Restri(var)[0]
    return vr[3]
def R6(var):
    vr = Restri(var)[0]
    return vr[4]
def R7(var):
    vr = Restri(var)[0]
    return vr[5]
def R8(var):
    vr = Restri(var)[0]
    return vr[6]
def R9(var):
    vr = Restri(var)[0]
    return vr[7]
def R10(var):
    vr = Restri(var)[0]
    return vr[8]
def R11(var):
    vr = Restri(var)[0]
    return vr[9]
def R12(var):
    vr = Restri(var)[0]
    return vr[10]
def R13(var):
    vr = Restri(var)[0]
    return vr[11]
def R14(var):
    vr = -var[0]
    return vr
def R15(var):
    vr = -var[1]
    return vr
def R16(var):
    vr = -var[2]
    return vr
def R17(var):
    vr = -var[3]
    return vr
def R18(var):
    vr = -var[4]
    return vr
def R19(var):
    vr = -var[5]
    return vr
def R20(var):
    vr = -var[6]
    return vr
def R21(var):
    vr = -var[7]
    return vr
def R22(var):
    vr = -var[8]
    return vr

cons = (#{'type': 'eq', 'fun': R1},
        {'type': 'ineq', 'fun': R2},
        {'type': 'ineq', 'fun': R3},
        {'type': 'ineq', 'fun': R4},
        {'type': 'ineq', 'fun': R5},
        {'type': 'ineq', 'fun': R6},
        {'type': 'ineq', 'fun': R7},
        {'type': 'ineq', 'fun': R8},
        {'type': 'ineq', 'fun': R9},
        {'type': 'ineq', 'fun': R10},
        {'type': 'ineq', 'fun': R11},
        {'type': 'ineq', 'fun': R12},
        {'type': 'ineq', 'fun': R13},
        {'type': 'ineq', 'fun': R14},
        {'type': 'ineq', 'fun': R15},
        {'type': 'ineq', 'fun': R16},
        {'type': 'ineq', 'fun': R17},
        {'type': 'ineq', 'fun': R18},
        {'type': 'ineq', 'fun': R19},
        {'type': 'ineq', 'fun': R20},
        {'type': 'ineq', 'fun': R21},
        {'type': 'ineq', 'fun': R22},)

var = [21, -10, -20, -10, 21, -20, -10, -20, 21]

solution = minimize(obj, var, method='SLSQP',constraints=cons)
a = list(solution.x)

data_opti = {"1": {str(i):round(a[abs(4-i)]) for i in range(4,7)},
        "2": {str(i):round(a[abs(4-i)+3]) for i in range(4,7)},
        "3": {str(i):round(a[abs(4-i)+6]) for i in range(4,7)},
        "4": {str(i+1):round(abs(a[abs(i*3)])) for i in range(0,3)},
        "5": {str(i+1):round(abs(a[abs(i*3)+1])) for i in range(0,3)},
        "6": {str(i+1):round(abs(a[abs(i*3)+2])) for i in range(0,3)}}

print("Agente 1 con:")
for i in range(4,7):
    print("\t Agente " + str(i) + ": " + str(a[abs(4-i)]))
print("Agente 2 con:")
for i in range(4,7):
    print("\t Agente " + str(i) + ": " + str(a[abs(4-i)+3])) 
print("Agente 3 con:")
for i in range(4,7):
    print("\t Agente " + str(i) + ": " + str(a[abs(4-i)+6]))

print("\n \n")
P_tri = Restri(a)[1]
for i in range(len(P_tri)):
    print("Agente " + str(i + 1) + ": " + str(P_tri[i]))

price = round(Price2(),2)
print("Precio: ", price)

###############################################################################
############### Pago de potencia a cada agente ################################
###############################################################################

#### Envio de valores a los agentes 


for publicador in publicadores:
    data = {"publicador": "admin", 
            "resultado":data_opti[publicador],
            "precio": price
            }
    publish(data,topics_public[publicador],broker)


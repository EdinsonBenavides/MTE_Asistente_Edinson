import requests


###### Autentication ####
url_autentication = "http://10.10.10.76:3601/api_authentication/"

# credentials 
credentials = {
  "email": "edinson@mte.com",
  "password": "edinson123"
}

# A GET request to the API
response = requests.post(url_autentication, json=credentials)

# Print the response
response_json = response.json()
token = response_json["token"]
print(token)
"""
##### obtener bloques ####

url_get_blocks= "http://10.10.10.76:3601/get_blocks/"

token = {
    'token': token
    }

# A GET request to the API
response = requests.post(url_get_blocks, json=token)

# Print the response
response_json = response.json()
print(response_json)
"""



##### Demandar energia #####

url_demand_energy= "http://10.10.10.76:3601/demand_energy/"

json_data = {
    "id_user": 1233193288,
    "demanda": 1150,
    "token": token
    }

# A GET request to the API
response = requests.post(url_demand_energy, json=json_data)

# Print the response
response_json = response.json()
print(response_json)

"""
##### agregar tokens #####

url_add_tokens= "http://10.10.10.76:3601/add_tokens/"

json_data = {
    "id_user": 1233193288,
    "amount": 500,
    "token": token
    }

# A GET request to the API
response = requests.post(url_add_tokens, json=json_data)

# Print the response
response_json = response.json()
print(response_json)
"""


"""

#### Hacer Trabsacciones ####
url_make_transaction= "http://10.10.10.76:3601/make_transaction/"

json_data = {
    "id_user": 1233193288,
    "id_user2": 1093458050,
    "energy": 100,
    "money": 0,
    "token": token
        }

# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json)

"""
"""
url_make_transaction= "http://10.10.10.76:3601/make_transaction/"

json_data = {
    "id_user": 1233193288,
    "id_user2": 1093458050,
    "energy": 101,
    "money": 0,
    "token": token
        }

# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json)
"""

"""
url_make_transaction= "http://10.10.10.76:3601/make_transaction/"

json_data = {
    "id_user": 1233193288,
    "id_user2": 1093458050,
    "energy": 202,
    "money": 0,
    "token": token
        }

# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json)
"""

"""
#### obtener transacciones ####

url_make_transaction= "http://10.10.10.76:3601/get_transactions/"

json_data = {
    "token": token
        }

# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json)
"""

"""
#### actualizar parametros #####
url_make_transaction = "http://10.10.10.76:3601/update_organization_values/"
"""
"""
Las variables no reciben valores decimales o de tipo flotante, unicamente
recibe valores enteros.
"""

"""
## Universidad de Nariño ##
json_data = {
  "id_organization": 1,
  "token": token,
  "cost_a": 6467,
  "cost_b": 79550,
  "cost_c": 115,
  "max_gen_limit": 500,
  "min_gen_limit":100,
  "total_power": 0
}


## CESMAG ##
json_data = {
  "id_organization": 2,
  "token": token,
  "cost_a": 6546,
  "cost_b": 144860,
  "cost_c": 82,
  "max_gen_limit": 362,
  "min_gen_limit":82,
  "total_power": 0
}

## Coperativa ##
json_data = {
  "id_organization": 3,
  "token": token,
  "cost_a": 19092,
  "cost_b": 83810,
  "cost_c": 153,
  "max_gen_limit": 315,
  "min_gen_limit":65,
  "total_power": 0
}


## Mariana ##
json_data = {
  "id_organization": 4,
  "token": token,
  "cost_a": 3919,
  "cost_b": 69610,
  "cost_c": 246,
  "max_gen_limit": 271,
  "min_gen_limit":50,
  "total_power": 0
}

## Departamental ##
json_data = {
  "id_organization": 5,
  "token": token,
  "cost_a": 10444,
  "cost_b": 115050,
  "cost_c": 0,
  "max_gen_limit": 60,
  "min_gen_limit":0,
  "total_power": 0
}




# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json)

"""

"""
#### Obtener valores de los parametros ####

url_make_transaction = "http://10.10.10.76:3601/get_org_values/"

json_data = {
  "id_organization": 2,
  "token": token
}

# A GET request to the API
response = requests.post(url_make_transaction, json=json_data)

# Print the response
response_json = response.json()
print(response_json[0]["id"])
"""
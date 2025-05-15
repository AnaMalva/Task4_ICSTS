import requests
import json
import sys
import os

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    
#------------------------------------------------ URL do servidor FHIR
url = "https://hapi.fhir.org/baseR4/"




#------------------- Headers que indicam que o pedido FHIR usa JSON
headers = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}



# url = "https://hapi.fhir.org/baseR4/Patient?name=paulo"
# patient_data = {
# }
# response = requests.get(url, data=json.dumps(patient_data), headers=headers)
# data = response.json()
# sys.exit()

#-----------------------Exemplo de um recurso Patient no formato FHIR
fhir_patient = {
	"resourceType": "Patient",
	 "name": [
		{ "family": "Carapau", "given": [ "Anastacio", "Manuel" ] } 
	],
	"gender": "male",
	"birthDate": "1974-12-25"
}


#------------------------------------- Observation
fhir_observation = {
	"resourceType": "Observation",
	"status": "final",
	"code": {
		"coding": [
			{
				"system": "http://loinc.org",
				"code": "29463-7",
				"display": "Body Weight"
			}
		]
	},
	"subject": {
		"reference": "Patient/47119777" #ID IMPORTANT
	},
	"effectiveDateTime": "2016-03-28",
	"valueQuantity": {
		"value": 85,
		"unit": "Kgs",
		"system": "http://unitsofmeasure.org",
		"code": "[lb_av]"
	}
}

#========================================================
# POST  
# ========================================================
#-------------------- Criar um patient - Enviando a requisição POST para o servidor FHIR

'''
url = "https://hapi.fhir.org/baseR4/Patient"
response = requests.post(url, data=json.dumps(fhir_patient), headers=headers)

# Verificando o status da resposta
if response.status_code == 201:
    data = response.json()
    resource_id = data.get("id")  # Supondo que o campo ID esteja no JSON
    #os.system('cls')
    print("-----------------------------------")
    print("Paciente criado com sucesso ID:",resource_id)
    print("-----------------------------------")
    print("Resposta do servidor:", data)
else:
    print("Erro ao criar o paciente.")
    print("Status:", response.status_code)
    print("Resposta:", response.text)

       
#========================================================
# GET ========================================================
#----------------- Aceder dados patient - Enviando a requisição POST para o servidor FHIR

url = "https://hapi.fhir.org/baseR4/Patient/47119777"
#url = "https://hapi.fhir.org/baseR4/Patient/"+str(resource_id)
response = requests.get(url, data=json.dumps(fhir_patient), headers=headers)
print(response.json())

#--------------------------- save the result - file patient.txt 
with open("patient.txt", 'w', encoding='utf-8') as file:
    json.dump(response.json(), file, indent=4)
resource_id = data.get("id")  # Supondo que o campo ID esteja no JSON

sys.exit()

'''

#===========================================================
# OBSERVATION 
#-------------------------------------- Criar observação  resource

url = "https://hapi.fhir.org/baseR4/Observation/"
response = requests.post(url, data=json.dumps(fhir_observation), headers=headers)
print("OBSERVATION :", response.status_code)
data = response.json()
resource_id = data.get("id")  # Supondo que o campo ID esteja no JSON

#===========================================================
#---------- Aceder observação
# GET
url = "https://hapi.fhir.org/baseR4/Observation/"+str(resource_id)
response = requests.get(url, data=json.dumps(fhir_patient), headers=headers)
print(response.json())

#--------------------------- save the result - file observation.txt 
with open("observation.txt", 'w', encoding='utf-8') as file:
    json.dump(response.json(), file, indent=4)

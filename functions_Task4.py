import requests
import json

def practitioner_upload(headers):

    fhir_practitioner = [
    {
        "resourceType": "Practitioner",
        "id": "pract-001",
        "name": [
            {
                "family": "Silva",
                "given": ["José", "Carlos"]
            }
        ],
        "gender": "male",
        "birthDate": "1985-06-15",
        "qualification": [
            {
                "code": {
                    "text": "Médico"
                },
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "+351912345678",
                "use": "work"
            }
        ]
    }
    ]

        
    url_medico = "https://hapi.fhir.org/baseR4/Practitioner"

    response = requests.post(url_medico, data=json.dumps(fhir_practitioner[0]), headers=headers)

    # Verificando o status da resposta
    if response.status_code == 201:
        data = response.json()
        practitioner_id = data.get("id")
        #os.system('cls')
        print("-----------------------------------")
        print("Médico criado com sucesso ID:",practitioner_id)
        print("-----------------------------------")
        print("Resposta do servidor:", data)
    else:
        print("Erro ao criar o médico.")
        print("Status:", response.status_code)
        print("Resposta:", response.text)
    print("----------------------------------------")

    return practitioner_id

def patient_upload(headers,num,practitioner_id):

    fhir_patient = [
    {
        "resourceType": "Patient",
        "name": [
            {"family": "Carapau", "given": ["Anastacio", "Manuel"]}
        ],
        "id": "patient-001",
        "gender": "male",
        "birthDate": "1974-12-25",
        "generalPractitioner": [{"reference": "Practitioner/" + str(practitioner_id)}]
    },
    {
        "resourceType": "Patient",
        "name": [
            {"family": "Silva", "given": ["Maria", "Joana"]}
        ],
        "id": "patient-002",
        "gender": "female",
        "birthDate": "1982-05-17",
        "generalPractitioner": [{"reference": "Practitioner/" + str(practitioner_id)}]
    },
    {
        "resourceType": "Patient",
        "name": [
            {"family": "Ferreira", "given": ["Carlos", "Eduardo"]}
        ],
        "id": "patient-003",
        "gender": "male",
        "birthDate": "1990-09-10",
        "generalPractitioner": [{"reference": "Practitioner/" + str(practitioner_id)}]
    },
        {
        "resourceType": "Patient",
        "name": [
            {"family": "Gois", "given": ["Luisa"]}
        ],
        "id": "patient-004",
        "gender": "female",
        "birthDate": "1978-03-22",
        "generalPractitioner": [{"reference": "Practitioner/" + str(practitioner_id)}]
    },
    {
        "resourceType": "Patient",
        "name": [
            {"family": "Pereira", "given": ["João", "Miguel"]}
        ],
        "id": "patient-005",
        "gender": "male",
        "birthDate": "1965-11-03",
        "generalPractitioner": [{"reference": "Practitioner/" + str(practitioner_id)}]
    }
    ]
        
    url_paciente = "https://hapi.fhir.org/baseR4/Patient"

    response = requests.post(url_paciente, data=json.dumps(fhir_patient[num-1]), headers=headers)

    # Verificando o status da resposta
    if response.status_code == 201:
        data = response.json()
        patient_id = data.get("id")
        #os.system('cls')
        print("-----------------------------------")
        print("Paciente criado com sucesso ID:",patient_id)
        print("-----------------------------------")
        print("Resposta do servidor:", data)
    else:
        print("Erro ao criar o paciente.")
        print("Status:", response.status_code)
        print("Resposta:", response.text)
    print("----------------------------------------")

    return patient_id

def observations_upload(headers, num, patient_id,diff_expiration,diff_inspiration):

    weigth=[85, 68, 90, 72, 93]
    height=[180, 170, 177, 168, 184]

    fhir_observations = [
    # diferença de expiração participante 1
       {
        "resourceType": "Observation",
    	"status": "final",
    	"code": {
    		"coding": [
    			{
    				"system": "http://loinc.org",
    				"code": "29463-7",
    				"display": "diferença de expiração"
    			}
    		]
    	},
    	"subject": {
    		"reference": "Patient/" + str(patient_id) #ID IMPORTANT
    	},
    	"effectiveDateTime": "2016-03-28",
    	"valueQuantity": {
    		"value": diff_expiration,
    		"unit": "∆Z",
    		"system": "http://unitsofmeasure.org", 
    		"code": "[lb_av]"}
        },
        {
        "resourceType": "Observation",
    	"status": "final",
    	"code": {
    		"coding": [
    			{
    				"system": "http://loinc.org",
    				"code": "29463-7",
    				"display": "diferença de expiração"
    			}
    		]
    	},
    	"subject": {
    		"reference": "Patient/" + str(patient_id) #ID IMPORTANT
    	},
    	"effectiveDateTime": "2016-03-28",
    	"valueQuantity": {
    		"value": weigth[num-1],
    		"unit": "kg",
    		"system": "http://unitsofmeasure.org", 
    		"code": "[lb_av]"}
            },
                    {
        "resourceType": "Observation",
    	"status": "final",
    	"code": {
    		"coding": [
    			{
    				"system": "http://loinc.org",
    				"code": "29463-7",
    				"display": "diferença de expiração"
    			}
    		]
    	},
    	"subject": {
    		"reference": "Patient/" + str(patient_id) #ID IMPORTANT
    	},
    	"effectiveDateTime": "2016-03-28",
    	"valueQuantity": {
    		"value": height[num-1],
    		"unit": "cm",
    		"system": "http://unitsofmeasure.org", 
    		"code": "[lb_av]"}
            },
    ]

    for obs in fhir_observations:
        url = "https://hapi.fhir.org/baseR4/Observation/" 
        response = requests.post(url, data=json.dumps(obs), headers=headers)
        data = response.json()
        resource_id = data.get("id")  # Supondo que o campo ID esteja no JSON 
        print("OBSERVATION :", resource_id)
        print("Resposta do servidor:", data)

def condition_upload(headers, patient_id, diag):
    fhir_conditions = [
      {
        "resourceType": "Condition",
        "id": "cond-001",
        "subject": {"reference": "Patient/patient-001"},
        "code": {"text": "Ventilação Pulmonar Simétrica"},
        "clinicalStatus": {"text": "active"},
        "verificationStatus": {"text": "confirmed"},
        "note": [{"text": "∆Z de expiração inferior a 0.5, o que indica simetria ventilatória."}],
        "onsetDateTime": "2025-05-14T00:00:00",
        "subject": {
    		"reference": "Patient/" + str(patient_id) #ID IMPORTANT
    	}
    },
    {
        "resourceType": "Condition",
        "id": "cond-002",
        "subject": {"reference": "Patient/patient-004"},
        "code": {"text": "Ventilação Pulmonar Assimétrica"},
        "clinicalStatus": {"text": "active"},
        "verificationStatus": {"text": "confirmed"},
        "note": [{"text": "∆Z de inspiração superior a 0.5, o que indica assimetria ventilatória e possível doença respiratória."}],
        "onsetDateTime": "2025-05-14T00:00:00",
        "subject": {
    		"reference": "Patient/" + str(patient_id) #ID IMPORTANT
    	}
    },]
    
    url = "https://hapi.fhir.org/baseR4/Condition/" 
    if diag==0:
        response = requests.post(url, data=json.dumps(fhir_conditions[diag]), headers=headers)
    else:
        response = requests.post(url, data=json.dumps(fhir_conditions[diag]), headers=headers)

        data = response.json()
        resource_id = data.get("id")  # Supondo que o campo ID esteja no JSON 
        print("CONDITION:", resource_id)
        print("Resposta do servidor:", data)

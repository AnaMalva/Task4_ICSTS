import os


from Task2.main_Task2 import *
from Task3.main_Task3 import *


from functions_Task4 import *

print("Que paciente vai testar?")
num=int(input())


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

base_url = "https://hapi.fhir.org/baseR4/"

headers = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

data=get_signal=()

diff_expiration,diff_inspiration, diag=get_data(num)

practitioner_id=practitioner_upload(headers)

patient_id=patient_upload(headers,num,practitioner_id)

observations_upload(headers, num, patient_id, diff_expiration, diff_inspiration)

condition_upload(headers, patient_id, diag)




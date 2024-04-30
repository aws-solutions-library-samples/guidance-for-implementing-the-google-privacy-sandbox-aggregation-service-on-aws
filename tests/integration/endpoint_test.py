import json
import random
import string
import time
from faker import Faker
import requests
from urllib.parse import urlparse
import sys



fake = Faker()

def generate_random_sentence():
    sentence_length = random.randint(5, 10)
    return ''.join(random.choice(string.ascii_letters) for _ in range(sentence_length))

def generate_sample_json():
    payload = generate_random_sentence()
    debug_cleartext_payload = payload
    
    sample_json = {
        "shared_info": json.dumps({
            "api": "attribution-reporting",
            "attribution_destination": fake.url(),
            "report_id": fake.uuid4(),
            "reporting_origin": fake.url(),
            "scheduled_report_time": str(fake.date_time().timestamp()),
            "source_registration_time": str(fake.date_time().timestamp()),
            "version": "1.0"
        }),
        "aggregation_service_payloads": [
            {
                "payload": payload,
                "key_id": fake.random_int(min=1, max=9),
                "debug_cleartext_payload": debug_cleartext_payload,
            }
        ],
        "aggregation_coordinator_origin": "https://publickeyservice.msmt.aws.privacysandboxservices.com",
        "source_debug_key": str(fake.random_int()),
        "trigger_debug_key": str(fake.random_int()),
        "trigger_context_id": str(fake.random_int()),
    }

    return json.dumps(sample_json)


if __name__ == '__main__':
    collector_alb = input("Please enter the URI to the ALB deployed by the CollectorService stack: ")
    parsed_url = urlparse(collector_alb)
    if not (parsed_url.scheme and parsed_url.netloc):
        print("Invalid URL. Exiting the program.")
        sys.exit(1)
    while True:
        data = generate_sample_json()
        response = requests.post(f"{collector_alb}/.well-known/attribution-reporting/report-aggregate-attribution",data)
        print(data)
        time.sleep(5)
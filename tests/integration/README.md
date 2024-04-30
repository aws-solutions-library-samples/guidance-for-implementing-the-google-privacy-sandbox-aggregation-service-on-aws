### Avro schema


```
{
  "type": "record",
  "name": "AggregationSchema",
  "namespace": "com.example",
  "fields": [
    {
      "name": "shared_info",
      "type": {
        "type": "string"
      }
    },
    {
      "name": "aggregation_service_payloads",
      "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "PayloadRecord",
          "fields": [
            {
              "name": "payload",
              "type": {
                "type":"string"
              }
            },
            {
              "name":"key_id",
              "type":{
               	"type":"string"
              }
            },
            {
             	"name":"debug_cleartext_payload",
              	"type":{
                	"type":"string"
              	}
            }
          ]
        }
      }
    },
    {
     	"name":"aggregation_coordinator_origin",
      	"type":{
        	"type":"string"
      	}
    },
    {
     	"name":"source_debug_key",
      	"type":{
        	"type":"string"
      	}
    },
    {
      	"name":"trigger_debug_key",
      	"type":{
        	"type":"string"
      	}
    },
    {
      	"name":"trigger_context_id",
      	"type":{
        	"type":"string"
     }
   }
 ]
}
```
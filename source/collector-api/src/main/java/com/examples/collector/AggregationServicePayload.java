package com.examples.collector;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class AggregationServicePayload {

    @JsonProperty("payload")
    private String payload;

    @JsonProperty("key_id")
    private String keyId;

    @JsonProperty("debug_cleartext_payload")
    private String debugCleartextPayload;
}



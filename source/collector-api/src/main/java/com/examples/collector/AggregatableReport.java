package com.examples.collector;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class AggregatableReport {

    @JsonProperty("source_site")
    private String sourceSite;

    @JsonProperty("attribution_destination")
    private String attributionDestination;

    @JsonProperty("shared_info")
    private String sharedInfo;

    @JsonProperty("aggregation_service_payloads")
    private List<AggregationServicePayload> aggregationServicePayloads;

    @JsonProperty("source_debug_key")
    private long sourceDebugKey;

    @JsonProperty("trigger_debug_key")
    private long triggerDebugKey;
}


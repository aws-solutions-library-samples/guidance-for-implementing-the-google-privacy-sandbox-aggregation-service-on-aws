package com.examples.collector;

import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Service;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

@Service
public class KinesisDataPublisher {

    private KinesisProducer producer;
    private final String streamName = "gps_aggregatable_report";
    private final ObjectMapper objectMapper = new ObjectMapper();

    @PostConstruct
    public void init() {
        this.producer = KinesisProducerConfig.createProducer();
    }

    @PreDestroy
    public void destroy() {
        producer.flushSync();
        producer.destroy();
    }

    public void sendJsonData(Object dataObject) {
        try {
            String jsonData = objectMapper.writeValueAsString(dataObject);
            ByteBuffer dataBuffer = ByteBuffer.wrap(jsonData.getBytes(StandardCharsets.UTF_8));
            String partitionKey = "partitionKey";

            producer.addUserRecord(streamName, partitionKey, dataBuffer);
        } catch (Exception e) {
            System.err.println("Error sending JSON data to Kinesis");
            e.printStackTrace();
        }
    }
}

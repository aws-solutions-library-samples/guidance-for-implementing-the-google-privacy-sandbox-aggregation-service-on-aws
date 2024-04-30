package com.examples.collector;

import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;

public class KinesisProducerConfig {
    public static KinesisProducer createProducer() {
        KinesisProducerConfiguration config = new KinesisProducerConfiguration()
                .setMaxConnections(1)
                .setRequestTimeout(60000)
                .setRecordMaxBufferedTime(15000);

        return new KinesisProducer(config);
    }
}

package com.examples.collector;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AggregationReportController {

    private final ObjectMapper objectMapper;
    private final KinesisDataPublisher kinesisDataPublisher;

    public AggregationReportController(
            KinesisDataPublisher kinesisDataPublisher,
            ObjectMapper objectMapper) {
        this.kinesisDataPublisher = kinesisDataPublisher;
        this.objectMapper = objectMapper;
    }


    @PostMapping("/.well-known/attribution-reporting/report-aggregate-attribution")
    public ResponseEntity<String> collectEndpoint(@RequestBody String rawReport, HttpServletRequest request) {
        try {
            AggregatableReport report = objectMapper.readValue(rawReport, AggregatableReport.class);
            kinesisDataPublisher.sendJsonData(report);
            return ResponseEntity.ok("Report processed successfully");
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error processing report: " + e.getMessage());
        }
    }

    @PostMapping("/.well-known/attribution-reporting/debug/report-aggregate-attribution")
    public ResponseEntity<String> debugCollectEndpoint(@RequestBody String rawReport, HttpServletRequest request) {
        try {
            AggregatableReport report = objectMapper.readValue(rawReport, AggregatableReport.class);
            kinesisDataPublisher.sendJsonData(report);
            return ResponseEntity.ok("Report processed successfully");
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error processing report: " + e.getMessage());
        }
    }
}

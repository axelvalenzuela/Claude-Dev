{
  "displayName": "${title}",
  "mosaicLayout": {
    "columns": 48,
    "tiles": [
      {
        "xPos": 0, "yPos": 0, "width": 16, "height": 16,
        "widget": {
          "title": "Tráfico por clase de respuesta (req/s)",
          "xyChart": {
            "dataSets": [{
              "plotType": "STACKED_AREA",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${run_service}\" AND metric.type=\"run.googleapis.com/request_count\"",
                  "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_RATE", "crossSeriesReducer": "REDUCE_SUM", "groupByFields": ["metric.label.response_code_class"] }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 16, "yPos": 0, "width": 16, "height": 16,
        "widget": {
          "title": "Latencia p50 / p95 / p99 (ms)",
          "xyChart": {
            "dataSets": [
              { "plotType": "LINE", "legendTemplate": "p50", "timeSeriesQuery": { "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${run_service}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_PERCENTILE_50", "crossSeriesReducer": "REDUCE_MEAN" } } } },
              { "plotType": "LINE", "legendTemplate": "p95", "timeSeriesQuery": { "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${run_service}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_PERCENTILE_95", "crossSeriesReducer": "REDUCE_MEAN" } } } },
              { "plotType": "LINE", "legendTemplate": "p99", "timeSeriesQuery": { "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${run_service}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_PERCENTILE_99", "crossSeriesReducer": "REDUCE_MEAN" } } } }
            ]
          }
        }
      },
      {
        "xPos": 32, "yPos": 0, "width": 16, "height": 16,
        "widget": {
          "title": "Saturación: instancias activas",
          "xyChart": {
            "dataSets": [{
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${run_service}\" AND metric.type=\"run.googleapis.com/container/instance_count\"",
                  "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_MAX", "crossSeriesReducer": "REDUCE_SUM" }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 0, "yPos": 16, "width": 24, "height": 16,
        "widget": {
          "title": "Burn rate del SLO de disponibilidad (1 h)",
          "xyChart": {
            "dataSets": [{
              "plotType": "LINE",
              "timeSeriesQuery": { "timeSeriesFilter": { "filter": "select_slo_burn_rate(\"${slo_name}\", \"3600s\")" } }
            }],
            "thresholds": [{ "value": 14.4, "label": "fast burn" }, { "value": 6, "label": "slow burn" }]
          }
        }
      },
      {
        "xPos": 24, "yPos": 16, "width": 24, "height": 16,
        "widget": {
          "title": "Uptime check /health (fracción de checks OK)",
          "xyChart": {
            "dataSets": [{
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.labels.check_id=\"${uptime_id}\" AND resource.type=\"uptime_url\"",
                  "aggregation": { "alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_FRACTION_TRUE", "crossSeriesReducer": "REDUCE_MEAN" }
                }
              }
            }]
          }
        }
      }
    ]
  }
}

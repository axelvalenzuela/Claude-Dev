{
  "widgets": [
    {
      "type": "text", "x": 0, "y": 0, "width": 24, "height": 2,
      "properties": { "markdown": "## Golden signals: ${api_name}/${api_stage}  |  SLO de disponibilidad ${slo_target}" }
    },
    {
      "type": "metric", "x": 0, "y": 2, "width": 8, "height": 6,
      "properties": {
        "title": "Tráfico (requests/min)", "region": "${region}", "stat": "Sum", "period": 60,
        "metrics": [ [ "AWS/ApiGateway", "Count", "ApiName", "${api_name}", "Stage", "${api_stage}" ] ]
      }
    },
    {
      "type": "metric", "x": 8, "y": 2, "width": 8, "height": 6,
      "properties": {
        "title": "Errores (tasa 5XX)", "region": "${region}", "period": 60,
        "metrics": [
          [ { "expression": "IF(r > 0, e / r * 100, 0)", "label": "% 5XX", "id": "rate" } ],
          [ "AWS/ApiGateway", "5XXError", "ApiName", "${api_name}", "Stage", "${api_stage}", { "id": "e", "stat": "Sum", "visible": false } ],
          [ "AWS/ApiGateway", "Count", "ApiName", "${api_name}", "Stage", "${api_stage}", { "id": "r", "stat": "Sum", "visible": false } ]
        ]
      }
    },
    {
      "type": "metric", "x": 16, "y": 2, "width": 8, "height": 6,
      "properties": {
        "title": "Latencia p50 / p90 / p99 (ms)", "region": "${region}", "period": 60,
        "metrics": [
          [ "AWS/ApiGateway", "Latency", "ApiName", "${api_name}", "Stage", "${api_stage}", { "stat": "p50" } ],
          [ "...", { "stat": "p90" } ],
          [ "...", { "stat": "p99" } ]
        ]
      }
    },
    {
      "type": "metric", "x": 0, "y": 8, "width": 12, "height": 6,
      "properties": {
        "title": "Saturación: throttles de Lambda y API 4XX", "region": "${region}", "stat": "Sum", "period": 60,
        "metrics": [
          [ "AWS/Lambda", "Throttles" ],
          [ "AWS/ApiGateway", "4XXError", "ApiName", "${api_name}", "Stage", "${api_stage}" ]
        ]
      }
    },
    {
      "type": "metric", "x": 12, "y": 8, "width": 12, "height": 6,
      "properties": {
        "title": "Synthetics: % éxito", "region": "${region}", "stat": "Average", "period": 300,
        "yAxis": { "left": { "min": 0, "max": 100 } },
        "metrics": [ [ "CloudWatchSynthetics", "SuccessPercent", "CanaryName", "${canary}" ] ]
      }
    }
  ]
}

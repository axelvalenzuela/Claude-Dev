{
  "Comment": "Pipeline de IA para documentos: extraer texto -> (entidades || resumen) -> guardar",
  "StartAt": "ExtractText",
  "States": {
    "ExtractText": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${extract_fn_arn}",
        "Payload": {
          "bucket.$": "$.detail.bucket.name",
          "key.$": "$.detail.object.key"
        }
      },
      "ResultSelector": {
        "bucket.$": "$.Payload.bucket",
        "key.$": "$.Payload.key",
        "text.$": "$.Payload.text"
      },
      "ResultPath": "$.doc",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.TooManyRequestsException", "Lambda.ServiceException", "States.Timeout"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2,
          "JitterStrategy": "FULL"
        }
      ],
      "Catch": [
        { "ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "NotifyFailure" }
      ],
      "Next": "Analyze"
    },
    "Analyze": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "DetectEntities",
          "States": {
            "DetectEntities": {
              "Type": "Task",
              "Resource": "arn:aws:states:::aws-sdk:comprehend:detectEntities",
              "Parameters": {
                "Text.$": "$.doc.text",
                "LanguageCode": "${language_code}"
              },
              "ResultSelector": { "entities.$": "$.Entities" },
              "End": true
            }
          }
        },
        {
          "StartAt": "Summarize",
          "States": {
            "Summarize": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Parameters": {
                "FunctionName": "${summarize_fn_arn}",
                "Payload": { "text.$": "$.doc.text" }
              },
              "ResultSelector": { "summary.$": "$.Payload.summary" },
              "Retry": [
                {
                  "ErrorEquals": ["States.TaskFailed"],
                  "IntervalSeconds": 5,
                  "MaxAttempts": 2,
                  "BackoffRate": 2
                }
              ],
              "End": true
            }
          }
        }
      ],
      "ResultPath": "$.analysis",
      "Catch": [
        { "ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "NotifyFailure" }
      ],
      "Next": "SaveResult"
    },
    "SaveResult": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Parameters": {
        "TableName": "${table_name}",
        "Item": {
          "document_id": { "S.$": "$.doc.key" },
          "bucket": { "S.$": "$.doc.bucket" },
          "summary": { "S.$": "$.analysis[1].summary" },
          "entities": { "S.$": "States.JsonToString($.analysis[0].entities)" },
          "processed_at": { "S.$": "$$.State.EnteredTime" },
          "execution": { "S.$": "$$.Execution.Id" }
        }
      },
      "End": true
    },
    "NotifyFailure": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "${alerts_topic_arn}",
        "Subject": "Falla en pipeline de documentos",
        "Message.$": "States.JsonToString($)"
      },
      "Next": "Failed"
    },
    "Failed": {
      "Type": "Fail",
      "Error": "DocumentPipelineFailed"
    }
  }
}

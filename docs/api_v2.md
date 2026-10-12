# SecureLex API v2 OpenAPI

Generated from the FastAPI OpenAPI schema. `/api/analyze` defaults to the legacy result. Set `api_version: 2` and supply a monotonically increasing `source_version` to select `AnalysisResultV2`; stage routes require `source_version`.

```json

{
  "openapi": "3.1.0",
  "info": {
    "title": "SecureLex IDE API",
    "description": "High-performance code security analysis and verified automated repair HTTP service.",
    "version": "0.1.0"
  },
  "paths": {
    "/api/health": {
      "get": {
        "summary": "Get Health",
        "description": "Return service health status, active version, and ML engine telemetry.",
        "operationId": "get_health_api_health_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HealthResponse"
                }
              }
            }
          }
        }
      }
    },
    "/api/capabilities": {
      "get": {
        "summary": "Get Capabilities",
        "description": "Report installed tools, language adapters and current provider availability.",
        "operationId": "get_capabilities_api_capabilities_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CapabilitiesResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/languages": {
      "get": {
        "summary": "Get Languages",
        "description": "List registered language plugins and editor syntax identifiers.",
        "operationId": "get_languages_api_languages_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/LanguageInfo"
                  },
                  "type": "array",
                  "title": "Response Get Languages Api Languages Get"
                }
              }
            }
          }
        }
      }
    },
    "/api/analyze": {
      "post": {
        "summary": "Analyze Code",
        "description": "api_version defaults to 1 and preserves the established response. Set api_version=2 and send source_version (incremented by the client on source edits) to receive AnalysisResultV2. The server echoes source_version and returns the SHA-256 source_hash.",
        "operationId": "analyze_code_api_analyze_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Legacy AnalysisResult by default; AnalysisResultV2 when api_version is 2.",
            "content": {
              "application/json": {
                "schema": {
                  "oneOf": [
                    {
                      "$ref": "#/components/schemas/AnalysisResult"
                    },
                    {
                      "$ref": "#/components/schemas/AnalysisResultV2"
                    }
                  ],
                  "description": "api_version=2 selects AnalysisResultV2; omitted or 1 preserves the legacy response."
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/analyze/lexical": {
      "post": {
        "summary": "Analyze Lexical",
        "operationId": "analyze_lexical_api_analyze_lexical_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/StageAnalysisResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        },
        "description": "source_version is required. The stage response reports unsupported or coupled work in omissions."
      }
    },
    "/api/analyze/syntax": {
      "post": {
        "summary": "Analyze Syntax",
        "operationId": "analyze_syntax_api_analyze_syntax_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/StageAnalysisResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        },
        "description": "source_version is required. The stage response reports unsupported or coupled work in omissions."
      }
    },
    "/api/analyze/security": {
      "post": {
        "summary": "Analyze Security",
        "operationId": "analyze_security_api_analyze_security_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/StageAnalysisResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        },
        "description": "source_version is required. The stage response reports unsupported or coupled work in omissions."
      }
    },
    "/api/analyze/quality": {
      "post": {
        "summary": "Analyze Quality",
        "operationId": "analyze_quality_api_analyze_quality_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/StageAnalysisResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        },
        "description": "source_version is required. The stage response reports unsupported or coupled work in omissions."
      }
    },
    "/api/ast/{analysis_id}/node/{node_id}": {
      "get": {
        "summary": "Get Ast Node",
        "description": "Expand a previously returned AST node id on demand.",
        "operationId": "get_ast_node_api_ast__analysis_id__node__node_id__get",
        "parameters": [
          {
            "name": "analysis_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Analysis Id"
            }
          },
          {
            "name": "node_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Node Id"
            }
          },
          {
            "name": "depth",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "default": 3,
              "title": "Depth"
            }
          },
          {
            "name": "max_nodes",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "default": 100,
              "title": "Max Nodes"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ASTViewV2"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/agent/status": {
      "get": {
        "summary": "Get Agent Status Endpoint",
        "description": "Return local agent status and local model availability.",
        "operationId": "get_agent_status_endpoint_api_agent_status_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AgentStatusResponse"
                }
              }
            }
          }
        }
      }
    },
    "/api/agent/analyze": {
      "post": {
        "summary": "Analyze Code Agent",
        "description": "Run code analysis with agent layer enabled (defaults to rules if set to off).",
        "operationId": "analyze_code_agent_api_agent_analyze_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AnalyzeRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AnalysisResult"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/fix": {
      "post": {
        "summary": "Apply Single Fix",
        "description": "Apply and verify a specific fix proposal.",
        "operationId": "apply_single_fix_api_fix_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FixRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FixResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/fix-all": {
      "post": {
        "summary": "Apply All Fixes",
        "description": "Iteratively apply all safe and verified fixes up to 3 passes.",
        "operationId": "apply_all_fixes_api_fix_all_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FixAllRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FixAllResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/feedback": {
      "post": {
        "summary": "Submit Feedback",
        "description": "Record user false-positive report to local append-only feedback storage.",
        "operationId": "submit_feedback_api_feedback_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FeedbackRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/FeedbackResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/samples": {
      "get": {
        "summary": "List Samples",
        "description": "Retrieve pre-bundled interactive code samples.",
        "operationId": "list_samples_api_samples_get",
        "parameters": [
          {
            "name": "language",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Language"
            }
          },
          {
            "name": "meta",
            "in": "query",
            "required": false,
            "schema": {
              "type": "boolean",
              "default": false,
              "title": "Meta"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/samples/{sample_id}": {
      "get": {
        "summary": "Sample Detail",
        "description": "Retrieve one shipped sample by ID.",
        "operationId": "sample_detail_api_samples__sample_id__get",
        "parameters": [
          {
            "name": "sample_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Sample Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SampleItem"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/ml/insights": {
      "post": {
        "summary": "Get Ml Insights",
        "description": "Compute per-feature-group occlusion explainability for a token window.",
        "operationId": "get_ml_insights_api_ml_insights_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/MLInsightsRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/MLInsightsResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/llm/status": {
      "get": {
        "summary": "Get Llm Status",
        "description": "Check whether an LLM provider is configured in environment variables.",
        "operationId": "get_llm_status_api_llm_status_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/LLMStatusResponse"
                }
              }
            }
          }
        }
      }
    },
    "/api/llm/fix": {
      "post": {
        "summary": "Request Llm Fix",
        "description": "Request and shadow-verify an AI-suggested remediation fix.",
        "operationId": "request_llm_fix_api_llm_fix_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/LLMFixRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/LLMFixResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/llm/explain": {
      "post": {
        "summary": "Request Llm Explain",
        "description": "Request plain-English explanation from configured LLM.",
        "operationId": "request_llm_explain_api_llm_explain_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/LLMExplainRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/LLMExplainResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/ai/consent": {
      "post": {
        "summary": "Set Ai Consent",
        "description": "Record or revoke remote source-processing consent for this server session.",
        "operationId": "set_ai_consent_api_ai_consent_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AIPermissionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "additionalProperties": true,
                  "type": "object",
                  "title": "Response Set Ai Consent Api Ai Consent Post"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/agent/events": {
      "get": {
        "summary": "Get Agent Events",
        "operationId": "get_agent_events_api_agent_events_get",
        "parameters": [
          {
            "name": "operation_id",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Operation Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/AgentEventResponse"
                  },
                  "title": "Response Get Agent Events Api Agent Events Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/ai/explain": {
      "post": {
        "summary": "Ai Explain",
        "description": "Explain a selected item from fresh deterministic evidence.",
        "operationId": "ai_explain_api_ai_explain_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AIExplainRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "additionalProperties": true,
                  "type": "object",
                  "title": "Response Ai Explain Api Ai Explain Post"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/ai/generate": {
      "post": {
        "summary": "Ai Generate",
        "description": "Generate a code draft, then run the deterministic analysis pipeline over it.",
        "operationId": "ai_generate_api_ai_generate_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AIGenerateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "additionalProperties": true,
                  "type": "object",
                  "title": "Response Ai Generate Api Ai Generate Post"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "AIExplainRequest": {
        "properties": {
          "session_id": {
            "type": "string",
            "maxLength": 128,
            "minLength": 16,
            "title": "Session Id"
          },
          "remote_consent": {
            "type": "boolean",
            "title": "Remote Consent",
            "default": false
          },
          "target": {
            "type": "string",
            "enum": [
              "token",
              "diagnostic",
              "finding",
              "file",
              "patch"
            ],
            "title": "Target"
          },
          "source": {
            "type": "string",
            "maxLength": 524288,
            "title": "Source"
          },
          "language": {
            "type": "string",
            "title": "Language"
          },
          "target_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Target Id"
          },
          "patch": {
            "anyOf": [
              {
                "type": "string",
                "maxLength": 131072
              },
              {
                "type": "null"
              }
            ],
            "title": "Patch"
          }
        },
        "type": "object",
        "required": [
          "session_id",
          "target",
          "source",
          "language"
        ],
        "title": "AIExplainRequest"
      },
      "AIGenerateRequest": {
        "properties": {
          "session_id": {
            "type": "string",
            "maxLength": 128,
            "minLength": 16,
            "title": "Session Id"
          },
          "remote_consent": {
            "type": "boolean",
            "title": "Remote Consent",
            "default": false
          },
          "language": {
            "type": "string",
            "enum": [
              "python",
              "java",
              "javascript",
              "cpp"
            ],
            "title": "Language"
          },
          "requirements": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "maxItems": 30,
            "minItems": 1,
            "title": "Requirements"
          }
        },
        "type": "object",
        "required": [
          "session_id",
          "language",
          "requirements"
        ],
        "title": "AIGenerateRequest"
      },
      "AIPermissionRequest": {
        "properties": {
          "session_id": {
            "type": "string",
            "maxLength": 128,
            "minLength": 16,
            "title": "Session Id"
          },
          "consent": {
            "type": "boolean",
            "title": "Consent"
          }
        },
        "type": "object",
        "required": [
          "session_id",
          "consent"
        ],
        "title": "AIPermissionRequest"
      },
      "ASTNodeV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "type": {
            "type": "string",
            "title": "Type"
          },
          "field_name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Field Name"
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "parent_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Parent Id"
          },
          "child_ids": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Child Ids"
          },
          "text_preview": {
            "type": "string",
            "title": "Text Preview"
          },
          "token_ids": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Token Ids"
          },
          "finding_ids": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Finding Ids"
          }
        },
        "type": "object",
        "required": [
          "id",
          "type",
          "range",
          "text_preview"
        ],
        "title": "ASTNodeV2"
      },
      "ASTViewV2": {
        "properties": {
          "root_id": {
            "type": "string",
            "title": "Root Id"
          },
          "nodes": {
            "items": {
              "$ref": "#/components/schemas/ASTNodeV2"
            },
            "type": "array",
            "title": "Nodes"
          },
          "truncated": {
            "type": "boolean",
            "title": "Truncated"
          },
          "node_limit": {
            "type": "integer",
            "title": "Node Limit"
          },
          "depth_limit": {
            "type": "integer",
            "title": "Depth Limit"
          }
        },
        "type": "object",
        "required": [
          "root_id",
          "nodes",
          "truncated",
          "node_limit",
          "depth_limit"
        ],
        "title": "ASTViewV2"
      },
      "AgentEventResponse": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "timestamp": {
            "type": "string",
            "title": "Timestamp"
          },
          "operation_id": {
            "type": "string",
            "title": "Operation Id"
          },
          "agent": {
            "type": "string",
            "title": "Agent"
          },
          "action": {
            "type": "string",
            "title": "Action"
          },
          "tool": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Tool"
          },
          "argument_summary": {
            "type": "string",
            "title": "Argument Summary"
          },
          "decision_source": {
            "type": "string",
            "title": "Decision Source"
          },
          "outcome": {
            "type": "string",
            "title": "Outcome"
          },
          "duration": {
            "type": "number",
            "title": "Duration"
          },
          "error": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Error"
          }
        },
        "type": "object",
        "required": [
          "id",
          "timestamp",
          "operation_id",
          "agent",
          "action",
          "tool",
          "argument_summary",
          "decision_source",
          "outcome",
          "duration"
        ],
        "title": "AgentEventResponse"
      },
      "AgentStatusResponse": {
        "properties": {
          "mode": {
            "type": "string",
            "title": "Mode"
          },
          "ollama_reachable": {
            "type": "boolean",
            "title": "Ollama Reachable"
          },
          "model": {
            "type": "string",
            "title": "Model"
          },
          "model_present": {
            "type": "boolean",
            "title": "Model Present"
          },
          "fallback_active": {
            "type": "boolean",
            "title": "Fallback Active"
          },
          "message": {
            "type": "string",
            "title": "Message",
            "default": ""
          }
        },
        "type": "object",
        "required": [
          "mode",
          "ollama_reachable",
          "model",
          "model_present",
          "fallback_active"
        ],
        "title": "AgentStatusResponse",
        "description": "Status of the local agent and local model provider."
      },
      "AnalysisDimension": {
        "properties": {
          "status": {
            "type": "string",
            "enum": [
              "ok",
              "issues",
              "incomplete",
              "unavailable"
            ],
            "title": "Status"
          },
          "reason": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Reason"
          }
        },
        "type": "object",
        "required": [
          "status"
        ],
        "title": "AnalysisDimension"
      },
      "AnalysisResult": {
        "properties": {
          "language": {
            "type": "string",
            "title": "Language"
          },
          "filename": {
            "type": "string",
            "title": "Filename"
          },
          "findings": {
            "items": {
              "$ref": "#/components/schemas/Finding"
            },
            "type": "array",
            "title": "Findings"
          },
          "tokens": {
            "items": {
              "$ref": "#/components/schemas/TokenInfo"
            },
            "type": "array",
            "title": "Tokens"
          },
          "summary": {
            "$ref": "#/components/schemas/AnalysisSummary"
          },
          "engine": {
            "$ref": "#/components/schemas/EngineMetadata"
          },
          "trace": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array",
            "title": "Trace"
          },
          "agent_meta": {
            "additionalProperties": true,
            "type": "object",
            "title": "Agent Meta"
          }
        },
        "type": "object",
        "required": [
          "language",
          "filename"
        ],
        "title": "AnalysisResult",
        "description": "Top-level container returned by Analyzer.analyze()."
      },
      "AnalysisSummary": {
        "properties": {
          "critical": {
            "type": "integer",
            "title": "Critical",
            "default": 0
          },
          "high": {
            "type": "integer",
            "title": "High",
            "default": 0
          },
          "medium": {
            "type": "integer",
            "title": "Medium",
            "default": 0
          },
          "low": {
            "type": "integer",
            "title": "Low",
            "default": 0
          },
          "info": {
            "type": "integer",
            "title": "Info",
            "default": 0
          },
          "score": {
            "type": "integer",
            "title": "Score",
            "default": 100
          },
          "tokens_total": {
            "type": "integer",
            "title": "Tokens Total",
            "default": 0
          },
          "tokens_malicious": {
            "type": "integer",
            "title": "Tokens Malicious",
            "default": 0
          },
          "tokens_suspicious": {
            "type": "integer",
            "title": "Tokens Suspicious",
            "default": 0
          },
          "lexical_errors": {
            "type": "integer",
            "title": "Lexical Errors",
            "default": 0
          },
          "syntax_errors": {
            "type": "integer",
            "title": "Syntax Errors",
            "default": 0
          }
        },
        "type": "object",
        "title": "AnalysisSummary",
        "description": "Summary counts and health score of an analysis run."
      },
      "AnalyzeOptions": {
        "properties": {
          "fixes": {
            "type": "boolean",
            "title": "Fixes",
            "default": true
          },
          "ml": {
            "type": "boolean",
            "title": "Ml",
            "default": true
          },
          "include_tokens": {
            "type": "boolean",
            "title": "Include Tokens",
            "default": true
          },
          "include_suppressed": {
            "type": "boolean",
            "title": "Include Suppressed",
            "default": false
          },
          "agent": {
            "type": "string",
            "title": "Agent",
            "default": "off"
          },
          "stages": {
            "items": {
              "type": "string",
              "enum": [
                "lexical",
                "syntax",
                "semantic",
                "security",
                "quality"
              ]
            },
            "type": "array",
            "title": "Stages"
          }
        },
        "type": "object",
        "title": "AnalyzeOptions",
        "description": "Analysis configuration options."
      },
      "AnalyzeRequest": {
        "properties": {
          "source": {
            "type": "string",
            "title": "Source"
          },
          "language": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Language"
          },
          "filename": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Filename"
          },
          "options": {
            "$ref": "#/components/schemas/AnalyzeOptions"
          },
          "api_version": {
            "type": "integer",
            "maximum": 2.0,
            "minimum": 1.0,
            "title": "Api Version",
            "default": 1
          },
          "source_version": {
            "type": "integer",
            "minimum": 0.0,
            "title": "Source Version",
            "default": 0
          },
          "include_ast": {
            "type": "boolean",
            "title": "Include Ast",
            "default": false
          },
          "ast_max_depth": {
            "type": "integer",
            "maximum": 20.0,
            "minimum": 1.0,
            "title": "Ast Max Depth",
            "default": 8
          },
          "ast_max_nodes": {
            "type": "integer",
            "maximum": 2000.0,
            "minimum": 1.0,
            "title": "Ast Max Nodes",
            "default": 500
          }
        },
        "type": "object",
        "required": [
          "source"
        ],
        "title": "AnalyzeRequest",
        "description": "Payload for code security analysis."
      },
      "CapabilitiesLanguage": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "name": {
            "type": "string",
            "title": "Name"
          },
          "extensions": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Extensions"
          },
          "monaco_id": {
            "type": "string",
            "title": "Monaco Id"
          },
          "lexer": {
            "additionalProperties": true,
            "type": "object",
            "title": "Lexer"
          },
          "parser": {
            "additionalProperties": true,
            "type": "object",
            "title": "Parser"
          },
          "semantic_tools": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Semantic Tools"
          },
          "security_tools": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Security Tools"
          },
          "formatter": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Formatter"
          }
        },
        "type": "object",
        "required": [
          "id",
          "name",
          "extensions",
          "monaco_id",
          "lexer",
          "parser",
          "semantic_tools",
          "security_tools",
          "formatter"
        ],
        "title": "CapabilitiesLanguage"
      },
      "CapabilitiesResponse": {
        "properties": {
          "version": {
            "type": "string",
            "title": "Version"
          },
          "languages": {
            "items": {
              "$ref": "#/components/schemas/CapabilitiesLanguage"
            },
            "type": "array",
            "title": "Languages"
          },
          "tools": {
            "items": {
              "$ref": "#/components/schemas/ToolStatus"
            },
            "type": "array",
            "title": "Tools"
          },
          "ai": {
            "additionalProperties": true,
            "type": "object",
            "title": "Ai"
          },
          "limits": {
            "additionalProperties": true,
            "type": "object",
            "title": "Limits"
          },
          "features": {
            "additionalProperties": true,
            "type": "object",
            "title": "Features"
          }
        },
        "type": "object",
        "required": [
          "version",
          "languages",
          "tools",
          "ai",
          "limits",
          "features"
        ],
        "title": "CapabilitiesResponse"
      },
      "DiagnosticV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "language": {
            "type": "string",
            "title": "Language"
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "category": {
            "type": "string",
            "enum": [
              "lexical",
              "syntax",
              "semantic",
              "security",
              "quality"
            ],
            "title": "Category"
          },
          "severity": {
            "type": "string",
            "title": "Severity"
          },
          "message": {
            "type": "string",
            "title": "Message"
          },
          "related_evidence": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Related Evidence"
          },
          "produced_by": {
            "type": "string",
            "title": "Produced By"
          },
          "certainty": {
            "type": "string",
            "enum": [
              "definitive",
              "heuristic",
              "incomplete"
            ],
            "title": "Certainty"
          }
        },
        "type": "object",
        "required": [
          "id",
          "language",
          "range",
          "category",
          "severity",
          "message",
          "produced_by",
          "certainty"
        ],
        "title": "DiagnosticV2"
      },
      "Edit": {
        "properties": {
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "new_text": {
            "type": "string",
            "title": "New Text"
          }
        },
        "type": "object",
        "required": [
          "range",
          "new_text"
        ],
        "title": "Edit",
        "description": "Atomic text edit replacing a Range with new text."
      },
      "EngineMetadata": {
        "properties": {
          "ml_mode": {
            "type": "string",
            "title": "Ml Mode",
            "default": "off"
          },
          "ml_model_id": {
            "type": "string",
            "title": "Ml Model Id",
            "default": "none"
          },
          "taint": {
            "type": "string",
            "title": "Taint",
            "default": "ast"
          },
          "version": {
            "type": "string",
            "title": "Version",
            "default": "0.1.0"
          },
          "elapsed_ms": {
            "type": "number",
            "title": "Elapsed Ms",
            "default": 0.0
          },
          "parser": {
            "type": "string",
            "title": "Parser",
            "default": "lexer-only"
          }
        },
        "type": "object",
        "title": "EngineMetadata",
        "description": "Metadata regarding engine execution and models used."
      },
      "FeedbackRequest": {
        "properties": {
          "finding_fingerprint": {
            "type": "string",
            "title": "Finding Fingerprint",
            "default": ""
          },
          "fingerprint": {
            "type": "string",
            "title": "Fingerprint",
            "default": ""
          },
          "rule_id": {
            "type": "string",
            "title": "Rule Id"
          },
          "language": {
            "type": "string",
            "title": "Language",
            "default": "python"
          },
          "verdict": {
            "type": "string",
            "title": "Verdict",
            "default": "false_positive"
          },
          "snippet": {
            "type": "string",
            "title": "Snippet",
            "default": ""
          },
          "note": {
            "type": "string",
            "title": "Note",
            "default": ""
          },
          "filename": {
            "type": "string",
            "title": "Filename",
            "default": "<editor>"
          },
          "line": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Line"
          }
        },
        "type": "object",
        "required": [
          "rule_id"
        ],
        "title": "FeedbackRequest",
        "description": "Payload for reporting a false-positive finding."
      },
      "FeedbackResponse": {
        "properties": {
          "saved": {
            "type": "boolean",
            "title": "Saved",
            "default": true
          }
        },
        "type": "object",
        "title": "FeedbackResponse",
        "description": "Response confirming persistence of feedback record."
      },
      "Finding": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "rule_id": {
            "type": "string",
            "title": "Rule Id"
          },
          "title": {
            "type": "string",
            "title": "Title",
            "default": ""
          },
          "cwe": {
            "type": "string",
            "title": "Cwe",
            "default": "CWE-000"
          },
          "severity": {
            "$ref": "#/components/schemas/Severity",
            "default": "medium"
          },
          "label": {
            "$ref": "#/components/schemas/Label",
            "default": "MALICIOUS"
          },
          "confidence": {
            "type": "number",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Confidence",
            "default": 0.8
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "message": {
            "type": "string",
            "title": "Message",
            "default": ""
          },
          "explanation": {
            "type": "string",
            "title": "Explanation",
            "default": ""
          },
          "evidence": {
            "additionalProperties": true,
            "type": "object",
            "title": "Evidence"
          },
          "taint_path": {
            "items": {
              "$ref": "#/components/schemas/TaintPathStep"
            },
            "type": "array",
            "title": "Taint Path"
          },
          "fixes": {
            "items": {
              "$ref": "#/components/schemas/Fix"
            },
            "type": "array",
            "title": "Fixes"
          },
          "sources": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Sources"
          },
          "suppressed": {
            "type": "boolean",
            "title": "Suppressed",
            "default": false
          },
          "suppression_reason": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Suppression Reason"
          },
          "kind": {
            "type": "string",
            "title": "Kind",
            "default": "security"
          },
          "attack": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Attack"
          },
          "exploitability": {
            "type": "number",
            "title": "Exploitability",
            "default": 0.5
          },
          "priority": {
            "type": "number",
            "title": "Priority",
            "default": 0.0
          },
          "simple_explanation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Simple Explanation"
          },
          "detailed_explanation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Detailed Explanation"
          }
        },
        "type": "object",
        "required": [
          "id",
          "rule_id",
          "range"
        ],
        "title": "Finding",
        "description": "A detected security issue, malicious pattern, or anomaly."
      },
      "Fix": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "finding_id": {
            "type": "string",
            "title": "Finding Id"
          },
          "title": {
            "type": "string",
            "title": "Title"
          },
          "description": {
            "type": "string",
            "title": "Description"
          },
          "confidence": {
            "type": "string",
            "title": "Confidence",
            "default": "safe"
          },
          "kind": {
            "type": "string",
            "title": "Kind",
            "default": "rule"
          },
          "edits": {
            "items": {
              "$ref": "#/components/schemas/Edit"
            },
            "type": "array",
            "title": "Edits"
          },
          "verification": {
            "$ref": "#/components/schemas/VerificationResult"
          }
        },
        "type": "object",
        "required": [
          "id",
          "finding_id",
          "title",
          "description",
          "verification"
        ],
        "title": "Fix",
        "description": "Remediation proposal with verified atomic edits."
      },
      "FixAllRequest": {
        "properties": {
          "source": {
            "type": "string",
            "title": "Source"
          },
          "language": {
            "type": "string",
            "title": "Language",
            "default": "python"
          },
          "filename": {
            "type": "string",
            "title": "Filename",
            "default": "<editor>"
          },
          "allow_review": {
            "type": "boolean",
            "title": "Allow Review",
            "default": false
          }
        },
        "type": "object",
        "required": [
          "source"
        ],
        "title": "FixAllRequest",
        "description": "Payload for multi-pass batch remediation."
      },
      "FixAllResponse": {
        "properties": {
          "new_source": {
            "type": "string",
            "title": "New Source"
          },
          "applied": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Applied"
          },
          "skipped": {
            "items": {
              "$ref": "#/components/schemas/SkippedFixItem"
            },
            "type": "array",
            "title": "Skipped"
          },
          "diff": {
            "type": "string",
            "title": "Diff"
          },
          "score_before": {
            "type": "integer",
            "title": "Score Before"
          },
          "score_after": {
            "type": "integer",
            "title": "Score After"
          }
        },
        "type": "object",
        "required": [
          "new_source",
          "applied",
          "skipped",
          "diff",
          "score_before",
          "score_after"
        ],
        "title": "FixAllResponse",
        "description": "Response returned from multi-pass batch remediation."
      },
      "FixRequest": {
        "properties": {
          "source": {
            "type": "string",
            "title": "Source"
          },
          "language": {
            "type": "string",
            "title": "Language",
            "default": "python"
          },
          "finding_id": {
            "type": "string",
            "title": "Finding Id"
          },
          "fix_id": {
            "type": "string",
            "title": "Fix Id"
          },
          "filename": {
            "type": "string",
            "title": "Filename",
            "default": "<editor>"
          }
        },
        "type": "object",
        "required": [
          "source",
          "finding_id",
          "fix_id"
        ],
        "title": "FixRequest",
        "description": "Payload to apply and verify a single specific fix."
      },
      "FixResponse": {
        "properties": {
          "new_source": {
            "type": "string",
            "title": "New Source"
          },
          "diff": {
            "type": "string",
            "title": "Diff"
          },
          "verification": {
            "$ref": "#/components/schemas/VerificationResult"
          },
          "new_result": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/AnalysisResult"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "type": "object",
        "required": [
          "new_source",
          "diff",
          "verification"
        ],
        "title": "FixResponse",
        "description": "Response returned after single fix application."
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "HealthResponse": {
        "properties": {
          "status": {
            "type": "string",
            "title": "Status",
            "default": "ok"
          },
          "version": {
            "type": "string",
            "title": "Version",
            "default": "0.1.0"
          },
          "ml_mode": {
            "type": "string",
            "title": "Ml Mode"
          },
          "ml_model_id": {
            "type": "string",
            "title": "Ml Model Id"
          }
        },
        "type": "object",
        "required": [
          "ml_mode",
          "ml_model_id"
        ],
        "title": "HealthResponse",
        "description": "System health and active telemetry status."
      },
      "LLMExplainRequest": {
        "properties": {
          "finding_id": {
            "type": "string",
            "title": "Finding Id"
          },
          "rule_id": {
            "type": "string",
            "title": "Rule Id"
          },
          "message": {
            "type": "string",
            "title": "Message",
            "default": ""
          }
        },
        "type": "object",
        "required": [
          "finding_id",
          "rule_id"
        ],
        "title": "LLMExplainRequest",
        "description": "Payload to request plain-English explanation."
      },
      "LLMExplainResponse": {
        "properties": {
          "explanation": {
            "type": "string",
            "title": "Explanation"
          },
          "error": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Error"
          }
        },
        "type": "object",
        "required": [
          "explanation"
        ],
        "title": "LLMExplainResponse",
        "description": "AI-generated plain English explanation."
      },
      "LLMFixRequest": {
        "properties": {
          "source": {
            "type": "string",
            "title": "Source"
          },
          "finding_id": {
            "type": "string",
            "title": "Finding Id"
          },
          "rule_id": {
            "type": "string",
            "title": "Rule Id"
          },
          "language": {
            "type": "string",
            "title": "Language",
            "default": "python"
          },
          "start_line": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Start Line"
          },
          "start_col": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Start Col"
          }
        },
        "type": "object",
        "required": [
          "source",
          "finding_id",
          "rule_id"
        ],
        "title": "LLMFixRequest",
        "description": "Payload to request an AI-suggested fix."
      },
      "LLMFixResponse": {
        "properties": {
          "fixes": {
            "items": {
              "$ref": "#/components/schemas/Fix"
            },
            "type": "array",
            "title": "Fixes"
          },
          "notes": {
            "type": "string",
            "title": "Notes",
            "default": ""
          }
        },
        "type": "object",
        "title": "LLMFixResponse",
        "description": "Fix response containing shadow-verified or advice-only proposals."
      },
      "LLMStatusResponse": {
        "properties": {
          "configured": {
            "type": "boolean",
            "title": "Configured"
          },
          "provider": {
            "type": "string",
            "title": "Provider"
          }
        },
        "type": "object",
        "required": [
          "configured",
          "provider"
        ],
        "title": "LLMStatusResponse",
        "description": "Configuration status for optional LLM assistant."
      },
      "Label": {
        "type": "string",
        "enum": [
          "MALICIOUS",
          "SUSPICIOUS",
          "SAFE"
        ],
        "title": "Label",
        "description": "Classification label for findings and tokens."
      },
      "LanguageInfo": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "display_name": {
            "type": "string",
            "title": "Display Name"
          },
          "extensions": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Extensions"
          },
          "monaco_id": {
            "type": "string",
            "title": "Monaco Id"
          }
        },
        "type": "object",
        "required": [
          "id",
          "display_name",
          "extensions",
          "monaco_id"
        ],
        "title": "LanguageInfo",
        "description": "Metadata for registered programming language plugin."
      },
      "MLInsightsRequest": {
        "properties": {
          "source": {
            "type": "string",
            "title": "Source"
          },
          "language": {
            "type": "string",
            "title": "Language",
            "default": "python"
          },
          "token_index": {
            "type": "integer",
            "title": "Token Index"
          }
        },
        "type": "object",
        "required": [
          "source",
          "token_index"
        ],
        "title": "MLInsightsRequest",
        "description": "Payload for per-token explainability inspection."
      },
      "MLInsightsResponse": {
        "properties": {
          "ml_mode": {
            "type": "string",
            "title": "Ml Mode"
          },
          "token_index": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Token Index"
          },
          "token_text": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Token Text"
          },
          "predicted_label": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Predicted Label"
          },
          "probabilities": {
            "anyOf": [
              {
                "additionalProperties": {
                  "type": "number"
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Probabilities"
          },
          "feature_group_drops": {
            "anyOf": [
              {
                "additionalProperties": {
                  "type": "number"
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Feature Group Drops"
          }
        },
        "type": "object",
        "required": [
          "ml_mode"
        ],
        "title": "MLInsightsResponse",
        "description": "Per-feature-group occlusion results for explainability."
      },
      "QualityObservationV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "kind": {
            "type": "string",
            "title": "Kind"
          },
          "range": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/Range"
              },
              {
                "type": "null"
              }
            ]
          },
          "value": {
            "title": "Value"
          },
          "evidence": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Evidence"
          },
          "measured": {
            "type": "boolean",
            "title": "Measured"
          }
        },
        "type": "object",
        "required": [
          "id",
          "kind",
          "measured"
        ],
        "title": "QualityObservationV2"
      },
      "Range": {
        "properties": {
          "start_line": {
            "type": "integer",
            "minimum": 1.0,
            "title": "Start Line",
            "description": "1-based start line number"
          },
          "start_col": {
            "type": "integer",
            "minimum": 1.0,
            "title": "Start Col",
            "description": "1-based start column in UTF-16 code units"
          },
          "end_line": {
            "type": "integer",
            "minimum": 1.0,
            "title": "End Line",
            "description": "1-based end line number"
          },
          "end_col": {
            "type": "integer",
            "minimum": 1.0,
            "title": "End Col",
            "description": "1-based end column in UTF-16 code units (exclusive)"
          }
        },
        "type": "object",
        "required": [
          "start_line",
          "start_col",
          "end_line",
          "end_col"
        ],
        "title": "Range",
        "description": "1-based text coordinates, end-exclusive, UTF-16 code units."
      },
      "SampleItem": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "title": {
            "type": "string",
            "title": "Title"
          },
          "category": {
            "type": "string",
            "title": "Category"
          },
          "language": {
            "type": "string",
            "title": "Language"
          },
          "filename": {
            "type": "string",
            "title": "Filename"
          },
          "code": {
            "type": "string",
            "title": "Code"
          },
          "description": {
            "type": "string",
            "title": "Description"
          },
          "group": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Group"
          },
          "kind": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Kind"
          },
          "level": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Level"
          },
          "topic": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Topic"
          },
          "summary": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Summary"
          },
          "notes": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notes"
          },
          "expect": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Expect"
          },
          "fix_expected": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Fix Expected"
          },
          "approximate": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "title": "Approximate"
          },
          "special_chars": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Special Chars"
          },
          "demo_order": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Demo Order"
          },
          "senior": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Senior"
          }
        },
        "type": "object",
        "required": [
          "id",
          "title",
          "category",
          "language",
          "filename",
          "code",
          "description"
        ],
        "title": "SampleItem",
        "description": "Interactive code sample for testing and IDE demonstration."
      },
      "SecurityFindingV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "rule_id": {
            "type": "string",
            "title": "Rule Id"
          },
          "title": {
            "type": "string",
            "title": "Title",
            "default": ""
          },
          "cwe": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Cwe"
          },
          "severity": {
            "$ref": "#/components/schemas/Severity",
            "default": "medium"
          },
          "label": {
            "$ref": "#/components/schemas/Label",
            "default": "MALICIOUS"
          },
          "confidence": {
            "type": "number",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Confidence",
            "default": 0.8
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "message": {
            "type": "string",
            "title": "Message",
            "default": ""
          },
          "explanation": {
            "type": "string",
            "title": "Explanation",
            "default": ""
          },
          "evidence": {
            "additionalProperties": true,
            "type": "object",
            "title": "Evidence"
          },
          "taint_path": {
            "items": {
              "$ref": "#/components/schemas/TaintPathStep"
            },
            "type": "array",
            "title": "Taint Path"
          },
          "fixes": {
            "items": {
              "$ref": "#/components/schemas/Fix"
            },
            "type": "array",
            "title": "Fixes"
          },
          "sources": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Sources"
          },
          "suppressed": {
            "type": "boolean",
            "title": "Suppressed",
            "default": false
          },
          "suppression_reason": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Suppression Reason"
          },
          "kind": {
            "type": "string",
            "title": "Kind",
            "default": "security"
          },
          "attack": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Attack"
          },
          "exploitability": {
            "type": "number",
            "title": "Exploitability",
            "default": 0.5
          },
          "priority": {
            "type": "number",
            "title": "Priority",
            "default": 0.0
          },
          "simple_explanation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Simple Explanation"
          },
          "detailed_explanation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Detailed Explanation"
          },
          "taint_path_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Taint Path Id"
          },
          "certainty": {
            "type": "string",
            "enum": [
              "definitive",
              "heuristic",
              "incomplete"
            ],
            "title": "Certainty",
            "default": "heuristic"
          },
          "remediation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Remediation"
          },
          "tool_provenance": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Tool Provenance"
          },
          "safe_pattern": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Safe Pattern"
          },
          "detectors_fired": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Detectors Fired"
          }
        },
        "type": "object",
        "required": [
          "id",
          "rule_id",
          "range"
        ],
        "title": "SecurityFindingV2"
      },
      "Severity": {
        "type": "string",
        "enum": [
          "critical",
          "high",
          "medium",
          "low",
          "info"
        ],
        "title": "Severity",
        "description": "Vulnerability severity levels."
      },
      "SkippedFixItem": {
        "properties": {
          "fix_id": {
            "type": "string",
            "title": "Fix Id"
          },
          "reason": {
            "type": "string",
            "title": "Reason"
          }
        },
        "type": "object",
        "required": [
          "fix_id",
          "reason"
        ],
        "title": "SkippedFixItem",
        "description": "Details of a skipped fix proposal."
      },
      "StageAnalysisResponse": {
        "properties": {
          "analysis_id": {
            "type": "string",
            "title": "Analysis Id"
          },
          "source_hash": {
            "type": "string",
            "title": "Source Hash"
          },
          "source_version": {
            "type": "integer",
            "title": "Source Version"
          },
          "language": {
            "type": "string",
            "title": "Language"
          },
          "stage": {
            "type": "string",
            "title": "Stage"
          },
          "lexical_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "syntax_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "semantic_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "tokens": {
            "items": {
              "$ref": "#/components/schemas/TokenV2"
            },
            "type": "array",
            "title": "Tokens"
          },
          "lexical_summary": {
            "additionalProperties": {
              "additionalProperties": {
                "type": "integer"
              },
              "type": "object"
            },
            "type": "object",
            "title": "Lexical Summary"
          },
          "ast": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/ASTViewV2"
              },
              {
                "type": "null"
              }
            ]
          },
          "diagnostics": {
            "items": {
              "$ref": "#/components/schemas/DiagnosticV2"
            },
            "type": "array",
            "title": "Diagnostics"
          },
          "findings": {
            "items": {
              "$ref": "#/components/schemas/SecurityFindingV2"
            },
            "type": "array",
            "title": "Findings"
          },
          "taint_paths": {
            "items": {
              "$ref": "#/components/schemas/TaintPathV2"
            },
            "type": "array",
            "title": "Taint Paths"
          },
          "quality": {
            "items": {
              "$ref": "#/components/schemas/QualityObservationV2"
            },
            "type": "array",
            "title": "Quality"
          },
          "findings_summary": {
            "additionalProperties": {
              "additionalProperties": {
                "type": "integer"
              },
              "type": "object"
            },
            "type": "object",
            "title": "Findings Summary"
          },
          "tools": {
            "items": {
              "$ref": "#/components/schemas/ToolStatus"
            },
            "type": "array",
            "title": "Tools"
          },
          "warnings": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Warnings"
          },
          "omissions": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Omissions"
          }
        },
        "type": "object",
        "required": [
          "analysis_id",
          "source_hash",
          "source_version",
          "language",
          "stage"
        ],
        "title": "StageAnalysisResponse"
      },
      "TaintPathStep": {
        "properties": {
          "step": {
            "$ref": "#/components/schemas/TaintStepKind"
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "text": {
            "type": "string",
            "title": "Text"
          },
          "note": {
            "type": "string",
            "title": "Note",
            "default": ""
          }
        },
        "type": "object",
        "required": [
          "step",
          "range",
          "text"
        ],
        "title": "TaintPathStep",
        "description": "Single step in a taint propagation path."
      },
      "TaintPathStepV2": {
        "properties": {
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "text": {
            "type": "string",
            "title": "Text"
          },
          "role": {
            "type": "string",
            "enum": [
              "source",
              "propagation",
              "sanitizer",
              "sink"
            ],
            "title": "Role"
          },
          "note": {
            "type": "string",
            "title": "Note",
            "default": ""
          }
        },
        "type": "object",
        "required": [
          "range",
          "text",
          "role"
        ],
        "title": "TaintPathStepV2"
      },
      "TaintPathV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "steps": {
            "items": {
              "$ref": "#/components/schemas/TaintPathStepV2"
            },
            "type": "array",
            "title": "Steps"
          },
          "complete": {
            "type": "boolean",
            "title": "Complete"
          },
          "limitation": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Limitation"
          }
        },
        "type": "object",
        "required": [
          "id",
          "steps",
          "complete"
        ],
        "title": "TaintPathV2"
      },
      "TaintStepKind": {
        "type": "string",
        "enum": [
          "source",
          "propagate",
          "sink",
          "sanitizer",
          "sanitizer_missing"
        ],
        "title": "TaintStepKind",
        "description": "Kinds of steps in a taint path."
      },
      "TokenInfo": {
        "properties": {
          "token": {
            "type": "string",
            "title": "Token"
          },
          "token_type": {
            "type": "string",
            "title": "Token Type"
          },
          "range": {
            "$ref": "#/components/schemas/Range"
          },
          "label": {
            "type": "string",
            "title": "Label",
            "default": "SAFE"
          },
          "score": {
            "type": "number",
            "title": "Score",
            "default": 0.0
          }
        },
        "type": "object",
        "required": [
          "token",
          "token_type",
          "range"
        ],
        "title": "TokenInfo",
        "description": "Token metadata reported in API responses."
      },
      "TokenV2": {
        "properties": {
          "id": {
            "type": "string",
            "title": "Id"
          },
          "language": {
            "type": "string",
            "title": "Language"
          },
          "lexeme": {
            "type": "string",
            "title": "Lexeme"
          },
          "token_type": {
            "type": "string",
            "title": "Token Type"
          },
          "category": {
            "type": "string",
            "title": "Category"
          },
          "start_offset": {
            "type": "integer",
            "minimum": 0.0,
            "title": "Start Offset",
            "description": "UTF-16 code-unit offset, zero-based"
          },
          "end_offset": {
            "type": "integer",
            "minimum": 0.0,
            "title": "End Offset",
            "description": "UTF-16 code-unit offset, zero-based, exclusive"
          },
          "start_offset_codepoint": {
            "type": "integer",
            "minimum": 0.0,
            "title": "Start Offset Codepoint",
            "description": "Python Unicode code-point offset, zero-based"
          },
          "end_offset_codepoint": {
            "type": "integer",
            "minimum": 0.0,
            "title": "End Offset Codepoint",
            "description": "Python Unicode code-point offset, zero-based, exclusive"
          },
          "start_line": {
            "type": "integer",
            "minimum": 1.0,
            "title": "Start Line"
          },
          "start_column": {
            "type": "integer",
            "minimum": 1.0,
            "title": "Start Column",
            "description": "UTF-16 code-unit column, one-based"
          },
          "end_line": {
            "type": "integer",
            "minimum": 1.0,
            "title": "End Line"
          },
          "end_column": {
            "type": "integer",
            "minimum": 1.0,
            "title": "End Column",
            "description": "UTF-16 code-unit column, one-based, exclusive"
          },
          "lexical_status": {
            "type": "string",
            "enum": [
              "valid",
              "invalid",
              "unknown"
            ],
            "title": "Lexical Status"
          },
          "diagnostic_ids": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Diagnostic Ids"
          }
        },
        "additionalProperties": false,
        "type": "object",
        "required": [
          "id",
          "language",
          "lexeme",
          "token_type",
          "category",
          "start_offset",
          "end_offset",
          "start_offset_codepoint",
          "end_offset_codepoint",
          "start_line",
          "start_column",
          "end_line",
          "end_column",
          "lexical_status"
        ],
        "title": "TokenV2"
      },
      "ToolStatus": {
        "properties": {
          "name": {
            "type": "string",
            "title": "Name"
          },
          "kind": {
            "type": "string",
            "title": "Kind"
          },
          "available": {
            "type": "boolean",
            "title": "Available"
          },
          "version": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Version"
          },
          "executed": {
            "type": "boolean",
            "title": "Executed",
            "default": false
          },
          "duration_ms": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "title": "Duration Ms"
          },
          "status": {
            "type": "string",
            "enum": [
              "ok",
              "failed",
              "timeout",
              "unavailable",
              "skipped"
            ],
            "title": "Status"
          },
          "reason": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Reason"
          }
        },
        "type": "object",
        "required": [
          "name",
          "kind",
          "available",
          "status"
        ],
        "title": "ToolStatus"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          },
          "input": {
            "title": "Input"
          },
          "ctx": {
            "type": "object",
            "title": "Context"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      },
      "VerificationResult": {
        "properties": {
          "syntax_ok": {
            "type": "boolean",
            "title": "Syntax Ok"
          },
          "finding_gone": {
            "type": "boolean",
            "title": "Finding Gone"
          },
          "new_findings": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "New Findings"
          },
          "verified": {
            "type": "boolean",
            "title": "Verified"
          },
          "notes": {
            "type": "string",
            "title": "Notes",
            "default": ""
          }
        },
        "type": "object",
        "required": [
          "syntax_ok",
          "finding_gone",
          "verified"
        ],
        "title": "VerificationResult",
        "description": "Result of fix safety and idempotency verification."
      },
      "AnalysisResultV2": {
        "properties": {
          "analysis_id": {
            "title": "Analysis Id",
            "type": "string"
          },
          "source_hash": {
            "pattern": "^[0-9a-f]{64}$",
            "title": "Source Hash",
            "type": "string"
          },
          "source_version": {
            "minimum": 0,
            "title": "Source Version",
            "type": "integer"
          },
          "language": {
            "title": "Language",
            "type": "string"
          },
          "lexical_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "syntax_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "semantic_status": {
            "$ref": "#/components/schemas/AnalysisDimension"
          },
          "tokens": {
            "items": {
              "$ref": "#/components/schemas/TokenV2"
            },
            "title": "Tokens",
            "type": "array"
          },
          "lexical_summary": {
            "additionalProperties": {
              "additionalProperties": {
                "type": "integer"
              },
              "type": "object"
            },
            "title": "Lexical Summary",
            "type": "object"
          },
          "syntax_diagnostics": {
            "items": {
              "$ref": "#/components/schemas/DiagnosticV2"
            },
            "title": "Syntax Diagnostics",
            "type": "array"
          },
          "semantic_diagnostics": {
            "items": {
              "$ref": "#/components/schemas/DiagnosticV2"
            },
            "title": "Semantic Diagnostics",
            "type": "array"
          },
          "security_findings": {
            "items": {
              "$ref": "#/components/schemas/SecurityFindingV2"
            },
            "title": "Security Findings",
            "type": "array"
          },
          "taint_paths": {
            "items": {
              "$ref": "#/components/schemas/TaintPathV2"
            },
            "title": "Taint Paths",
            "type": "array"
          },
          "quality": {
            "items": {
              "$ref": "#/components/schemas/QualityObservationV2"
            },
            "title": "Quality",
            "type": "array"
          },
          "tools": {
            "items": {
              "$ref": "#/components/schemas/ToolStatus"
            },
            "title": "Tools",
            "type": "array"
          },
          "timing": {
            "additionalProperties": {
              "type": "number"
            },
            "title": "Timing",
            "type": "object"
          },
          "warnings": {
            "items": {
              "type": "string"
            },
            "title": "Warnings",
            "type": "array"
          },
          "omissions": {
            "items": {
              "type": "string"
            },
            "title": "Omissions",
            "type": "array"
          }
        },
        "required": [
          "analysis_id",
          "source_hash",
          "source_version",
          "language"
        ],
        "title": "AnalysisResultV2",
        "type": "object"
      }
    }
  }
}
```

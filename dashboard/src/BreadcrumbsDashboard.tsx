import React, { useState, useEffect } from "react";

const Clock = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <circle cx="12" cy="12" r="10" />
    <polyline points="12,6 12,12 16,14" />
  </svg>
);

const Zap = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2" />
  </svg>
);

const DollarSign = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

const MessageSquare = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const Wrench = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
  </svg>
);

const Activity = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
  </svg>
);

const RefreshCw = ({ size = 16, style = {} }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    style={style}
  >
    <polyline points="23,4 23,10 17,10" />
    <polyline points="1,20 1,14 7,14" />
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
  </svg>
);

const Upload = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7,10 12,5 17,10" />
    <line x1="12" y1="5" x2="12" y2="15" />
  </svg>
);

interface LogEntry {
  action_id: string;
  session_id: string;
  timestamp: string;
  action_type: string;
  input_data: string;
  output_data: string;
  model_name: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cost_usd: number | null;
  duration_ms: number | null;
  metadata: string;
}

const BreadcrumbsDashboard = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [sessions, setSessions] = useState<{ [key: string]: LogEntry[] }>({});
  const [hoveredLog, setHoveredLog] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string>("");
  const [fileHandle, setFileHandle] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const readLocalFile = (file: File): Promise<LogEntry[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csvText = e.target?.result as string;
          console.log("Reading file:", file.name);

          const lines = csvText.split("\n").filter((line) => line.trim());
          if (lines.length === 0) return resolve([]);

          const headers = lines[0]
            .split(",")
            .map((h) => h.trim().replace(/"/g, ""));

          const logs: LogEntry[] = lines.slice(1).map((line) => {
            const values = [];
            let current = "";
            let inQuotes = false;

            for (let i = 0; i < line.length; i++) {
              const char = line[i];
              if (char === '"') {
                inQuotes = !inQuotes;
              } else if (char === "," && !inQuotes) {
                values.push(current.trim());
                current = "";
              } else {
                current += char;
              }
            }
            values.push(current.trim());

            const logEntry: any = {};
            headers.forEach((header, index) => {
              let value = values[index] || "";
              value = value.replace(/^"|"$/g, "");

              switch (header) {
                case "prompt_tokens":
                case "completion_tokens":
                case "total_tokens":
                  logEntry[header] =
                    value && value !== "" ? parseInt(value) : null;
                  break;
                case "cost_usd":
                case "duration_ms":
                  logEntry[header] =
                    value && value !== "" ? parseFloat(value) : null;
                  break;
                default:
                  logEntry[header] = value;
              }
            });

            return logEntry as LogEntry;
          });

          const validLogs = logs.filter(
            (log) => log.action_id && log.action_id.trim() !== ""
          );
          console.log(`Loaded ${validLogs.length} valid logs`);
          resolve(validLogs);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsText(file);
    });
  };

  const supportsTrueRefresh = "showOpenFilePicker" in window;

  const handleFileSelect = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (file && file.type === "text/csv") {
      setSelectedFile(file);
      setSelectedFilePath(file.name);

      // Try to get file handle for live refresh (Chrome/Edge only)
      if (supportsTrueRefresh) {
        try {
          console.log("Auto-enabling true refresh for Chrome/Edge...");
          const [handle] = await (window as any).showOpenFilePicker({
            types: [
              {
                description: "CSV files",
                accept: { "text/csv": [".csv"] },
              },
            ],
            multiple: false,
          });

          setFileHandle(handle);
          const handleFile = await handle.getFile();
          setSelectedFile(handleFile);
          setSelectedFilePath(handleFile.name);
          await loadDataFromFile(handleFile);
          console.log("True refresh enabled automatically!");
          return;
        } catch (error) {
          console.log("User cancelled file handle request, using basic mode");
        }
      }

      loadDataFromFile(file);
    }
    // Reset input so same file can be selected again
    event.target.value = "";
  };

  const loadDataFromFile = async (file: File) => {
    setIsLoading(true);
    try {
      const csvLogs = await readLocalFile(file);
      setLogs(csvLogs);
      setLastUpdated(new Date());

      // Group by session
      const sessionGroups = csvLogs.reduce((acc, log) => {
        if (!acc[log.session_id]) {
          acc[log.session_id] = [];
        }
        acc[log.session_id].push(log);
        return acc;
      }, {} as { [key: string]: LogEntry[] });

      setSessions(sessionGroups);
    } catch (error) {
      console.error("Error loading file:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!selectedFile) return;

    setIsRefreshing(true);
    console.log("Refreshing file:", selectedFilePath);

    try {
      // Use file handle for live refresh if available
      if (fileHandle && "getFile" in fileHandle) {
        try {
          console.log("Using file handle to get fresh content from disk...");
          const freshFile = await fileHandle.getFile();
          setSelectedFile(freshFile);
          await loadDataFromFile(freshFile);
          console.log("TRUE REFRESH SUCCESS - loaded fresh data from disk!");
          return;
        } catch (error) {
          console.log("File handle refresh failed:", error);
        }
      }

      // Fallback: re-process existing file
      console.log("No file handle available - re-processing existing data...");
      await loadDataFromFile(selectedFile);
      console.log("Re-processed existing file data");
    } catch (error) {
      console.error("Refresh failed:", error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatCurrency = (amount: number | null) => {
    return amount ? `$${amount.toFixed(6)}` : "N/A";
  };

  const formatDuration = (ms: number | null) => {
    return ms ? `${ms.toFixed(0)}ms` : "N/A";
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case "llm_call":
        return <MessageSquare size={16} />;
      case "tool_use":
        return <Wrench size={16} />;
      default:
        return <Activity size={16} />;
    }
  };

  const parseJsonSafely = (jsonString: string) => {
    try {
      return JSON.parse(jsonString);
    } catch {
      return {};
    }
  };

  const extractUserInput = (inputData: string) => {
    console.log("Raw input data:", inputData);

    try {
      // First try to parse as JSON
      const parsed = JSON.parse(inputData);
      console.log("Parsed as JSON:", parsed);

      if (parsed.prompt) {
        return parsed;
      }
    } catch (error) {
      console.log("Standard JSON parsing failed, trying to fix format...");

      try {
        // Fix format like: {prompt: value, tool_responses: [1,2]}
        // to: {"prompt": "value", "tool_responses": [1,2]}
        let fixedJson = inputData
          .replace(/\{(\w+):/g, '{"$1":') // {prompt: -> {"prompt":
          .replace(/,\s*(\w+):/g, ', "$1":') // , tool_responses: -> , "tool_responses":
          .replace(/:\s*([^,\[\]{}]+)(?=[,}])/g, ': "$1"') // : value -> : "value" (but not arrays/objects)
          .replace(/:\s*(\[[^\]]+\])/g, ": $1"); // Keep arrays as-is

        console.log("Fixed JSON:", fixedJson);

        const parsed = JSON.parse(fixedJson);
        console.log("Successfully parsed fixed JSON:", parsed);

        return parsed;
      } catch (fixError) {
        console.log("Failed to fix JSON format:", fixError);

        const result = { prompt: "Unknown input" };

        const promptMatch = inputData.match(/prompt:\s*([^,}]+)/);
        if (promptMatch) {
          result.prompt = promptMatch[1].trim();
        }

        const toolMatch = inputData.match(/tool_responses:\s*\[([^\]]+)\]/);
        if (toolMatch) {
          const toolValues = toolMatch[1].split(",").map((v) => v.trim());
          result.tool_responses = toolValues;
        }

        console.log("Manual parsing result:", result);
        return result;
      }
    }

    return { prompt: inputData || "Unknown input" };
  };

  const renderStructuredInput = (inputData: any) => {
    if (typeof inputData === "string") {
      return inputData;
    }

    if (typeof inputData === "object" && inputData !== null) {
      const getFieldColor = (fieldName: string) => {
        const colorMap = {
          system: "#a78bfa", // Purple
          human: "#60a5fa", // Blue
          user: "#60a5fa", // Blue (alias for human)
          prompt: "#60a5fa", // Blue
          ai: "#34d399", // Green
          assistant: "#34d399", // Green (alias for ai)
          tool: "#fbbf24", // Yellow/Orange
          tool_responses: "#34d399", // Green
          tool_results: "#34d399", // Green
        };

        return colorMap[fieldName.toLowerCase()] || "#9ca3af"; // Default gray
      };

      const cleanText = (text: string) => {
        return text.replace(/\\u([0-9a-fA-F]{4})/g, (match, code) =>
          String.fromCharCode(parseInt(code, 16))
        );
      };

      const specialFields = ["tool_responses", "tool_results"];
      const regularFields = Object.keys(inputData).filter(
        (key) => !specialFields.includes(key)
      );

      return (
        <div>
          {regularFields.map((fieldName) => {
            const value = inputData[fieldName];

            if (!value || (typeof value === "string" && value.trim() === "")) {
              return null;
            }

            const displayValue =
              typeof value === "string"
                ? cleanText(value)
                : JSON.stringify(value);

            return (
              <div key={fieldName} style={{ marginBottom: "8px" }}>
                <span
                  style={{ fontWeight: "600", color: getFieldColor(fieldName) }}
                >
                  {fieldName}
                </span>
                <span style={{ color: "#9ca3af" }}>: </span>
                <span>{displayValue}</span>
              </div>
            );
          })}

          {/* Handle tool responses/results specially */}
          {(inputData.tool_responses || inputData.tool_results) && (
            <div>
              <span style={{ fontWeight: "600", color: "#34d399" }}>
                {inputData.tool_responses ? "tool responses" : "tool results"}
              </span>
              <span style={{ color: "#9ca3af" }}>: </span>
              <span style={{ color: "#fbbf24" }}>
                [
                {(inputData.tool_responses || inputData.tool_results).join(
                  ", "
                )}
                ]
              </span>
            </div>
          )}
        </div>
      );
    }

    return String(inputData);
  };

  const extractResponse = (outputData: string) => {
    try {
      const parsed = JSON.parse(outputData);

      if (parsed.response) {
        return { response: parsed.response };
      }

      return parsed;
    } catch (error) {
         try {
         let fixedJson = outputData
          .replace(/\{(\w+):/g, '{"$1":') // {response: -> {"response":
          .replace(/,\s*(\w+):/g, ', "$1":') // , other_prop: -> , "other_prop":
          .replace(/:\s*([^,\[\]{}]+)(?=[,}])/g, ': "$1"') // : value -> : "value" (but not arrays/objects)
          .replace(/:\s*(\[[^\]]+\])/g, ": $1"); // Keep arrays as-is

        const parsed = JSON.parse(fixedJson);

        if (parsed.response) {
          let cleanResponse = parsed.response;

          cleanResponse = cleanResponse.replace(
            /\\\\u([0-9a-fA-F]{4})/g,
            (match, code) => {
              return String.fromCharCode(parseInt(code, 16));
            }
          );

          cleanResponse = cleanResponse.replace(
            /\\u([0-9a-fA-F]{4})/g,
            (match, code) => {
              return String.fromCharCode(parseInt(code, 16));
            }
          );

          cleanResponse = cleanResponse.replace(/\\\\/g, "\\");

          return { response: cleanResponse };
        }

        return parsed;
      } catch (fixError) {
        const result = { response: "Unknown response" };

        const responseMatch = outputData.match(/response:\s*(.+)$/);
        if (responseMatch) {
          let response = responseMatch[1].trim();

          // Clean up Unicode escapes
          response = response.replace(/\\u([0-9a-fA-F]{4})/g, (match, code) =>
            String.fromCharCode(parseInt(code, 16))
          );

          result.response = response;
        }

        return result;
      }
    }
  };

  const renderStructuredResponse = (responseData: any) => {
    if (typeof responseData === "string") {
      const toolInfo = parseToolCalls(responseData);

      if (toolInfo.hasTools) {
        return (
          <div>
            <div style={{ marginBottom: "8px", color: "#fbbf24" }}>
              🔧 Tool calls:
            </div>
            <ul style={{ margin: "0", paddingLeft: "20px", color: "#34d399" }}>
              {toolInfo.tools.map((tool, index) => (
                <li key={index} style={{ marginBottom: "4px" }}>
                  <code
                    style={{
                      backgroundColor: "rgba(52, 211, 153, 0.1)",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontFamily: "monospace",
                      fontSize: "13px",
                    }}
                  >
                    {tool}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        );
      } else {
        return responseData;
      }
    }

    if (responseData.response) {
      const toolInfo = parseToolCalls(responseData.response);

      if (toolInfo.hasTools) {
        return (
          <div>
            <div style={{ marginBottom: "8px", color: "#fbbf24" }}>
              🔧 Tool calls:
            </div>
            <ul style={{ margin: "0", paddingLeft: "20px", color: "#34d399" }}>
              {toolInfo.tools.map((tool, index) => (
                <li key={index} style={{ marginBottom: "4px" }}>
                  <code
                    style={{
                      backgroundColor: "rgba(52, 211, 153, 0.1)",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontFamily: "monospace",
                      fontSize: "13px",
                    }}
                  >
                    {tool}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        );
      } else {
        return (
          <div>
            <span style={{ fontWeight: "600", color: "#60a5fa" }}>
              response
            </span>
            <span style={{ color: "#9ca3af" }}>: </span>
            <span>{responseData.response}</span>
          </div>
        );
      }
    }

    return JSON.stringify(responseData);
  };

  const parseToolCalls = (response: string) => {
    // Check if response contains tool calls
    const toolPattern = /🔧\s*Decided to call tools?:\s*(.+)/;
    const match = response.match(toolPattern);

    if (match) {
      const toolsText = match[1];

      // Extract individual tool calls like: get_weather(city=London), convert_currency(amount=500, from_currency=USD, to_currency=GBP)
      const toolCalls = toolsText.split(/,\s*(?=[a-zA-Z_][a-zA-Z0-9_]*\()/);

      return {
        hasTools: true,
        tools: toolCalls.map((tool) => tool.trim()),
        originalResponse: response,
      };
    }

    return {
      hasTools: false,
      tools: [],
      originalResponse: response,
    };
  };

  const getTotalStats = () => {
    const totalCost = logs.reduce((sum, log) => sum + (log.cost_usd || 0), 0);
    const totalTokens = logs.reduce(
      (sum, log) => sum + (log.total_tokens || 0),
      0
    );
    const avgDuration =
      logs.length > 0
        ? logs.reduce((sum, log) => sum + (log.duration_ms || 0), 0) /
          logs.length
        : 0;

    return { totalCost, totalTokens, avgDuration };
  };

  const getSessionPreview = (sessionLogs: LogEntry[]) => {
    // Find first LLM call to get user input preview
    const firstLlmCall = sessionLogs.find(
      (log) => log.action_type === "llm_call"
    );
    if (firstLlmCall) {
      const userInputData = extractUserInput(firstLlmCall.input_data);

      // Extract just the prompt for preview (truncate for sidebar)
      const promptText =
        typeof userInputData === "string"
          ? userInputData
          : userInputData.prompt || "Unknown input";
      return promptText.length > 60
        ? promptText.substring(0, 60) + "..."
        : promptText;
    }
    return "No user input found";
  };

  // Auto-select first session when sessions load
  useEffect(() => {
    const sessionIds = Object.keys(sessions);
    if (sessionIds.length > 0 && !selectedSession) {
      setSelectedSession(sessionIds[0]);
    }
  }, [sessions, selectedSession]);

  const stats = getTotalStats();

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#111827",
        color: "#f9fafb",
      }}
    >
      {/* Header */}
      <div
        style={{
          borderBottom: "1px solid #374151",
          backgroundColor: "rgba(31, 41, 55, 0.5)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div
          style={{
            maxWidth: "1280px",
            margin: "0 auto",
            padding: "16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Activity size={32} color="#60a5fa" />
            <div>
              <h1
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: "#ffffff",
                  margin: 0,
                }}
              >
                Agent Breadcrumbs
              </h1>
              <p style={{ color: "#9ca3af", fontSize: "14px", margin: 0 }}>
                Local CSV file viewer
              </p>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                style={{ display: "none" }}
                id="csvFileInput"
              />
              <label
                htmlFor="csvFileInput"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  backgroundColor: "#60a5fa",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "500",
                  transition: "background-color 0.2s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#3b82f6")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "#60a5fa")
                }
              >
                <Upload size={16} />
                Select CSV File
              </label>

              {supportsTrueRefresh && (
                <button
                  onClick={handleRefresh}
                  disabled={!selectedFile || isRefreshing}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    backgroundColor:
                      !selectedFile || isRefreshing ? "#6b7280" : "#059669",
                    color:
                      !selectedFile || isRefreshing ? "#9ca3af" : "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    padding: "8px 12px",
                    cursor:
                      !selectedFile || isRefreshing ? "not-allowed" : "pointer",
                    fontSize: "14px",
                    fontWeight: "500",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = "#047857";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!e.currentTarget.disabled) {
                      e.currentTarget.style.backgroundColor = "#059669";
                    }
                  }}
                >
                  <RefreshCw
                    size={16}
                    style={{
                      animation: isRefreshing
                        ? "spin 1s linear infinite"
                        : "none",
                    }}
                  />
                  {isRefreshing ? "Refreshing..." : "Refresh"}
                </button>
              )}

              {!supportsTrueRefresh && selectedFile && (
                <div
                  style={{
                    backgroundColor: "#374151",
                    color: "#9ca3af",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    border: "1px solid #4b5563",
                  }}
                >
                  💡 Use Chrome/Edge for live refresh feature
                </div>
              )}
            </div>

            {lastUpdated && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontSize: "14px",
                  color: "#9ca3af",
                }}
              >
                <Clock size={16} />
                <span>Updated: {lastUpdated.toLocaleTimeString()}</span>
              </div>
            )}

            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                style={{
                  backgroundColor: "#1f2937",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid #374151",
                  textAlign: "center",
                  minWidth: "60px",
                }}
              >
                <span
                  style={{
                    color: "#9ca3af",
                    fontSize: "11px",
                    display: "block",
                    marginBottom: "2px",
                  }}
                >
                  Sessions
                </span>
                <div
                  style={{
                    fontSize: "16px",
                    fontWeight: "600",
                    color: "#60a5fa",
                  }}
                >
                  {Object.keys(sessions).length}
                </div>
              </div>
              <div
                style={{
                  backgroundColor: "#1f2937",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid #374151",
                  textAlign: "center",
                  minWidth: "60px",
                }}
              >
                <span
                  style={{
                    color: "#9ca3af",
                    fontSize: "11px",
                    display: "block",
                    marginBottom: "2px",
                  }}
                >
                  Logs
                </span>
                <div
                  style={{
                    fontSize: "16px",
                    fontWeight: "600",
                    color: "#34d399",
                  }}
                >
                  {logs.length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* File Info Bar */}
      {selectedFile && (
        <div
          style={{
            backgroundColor: "rgba(31, 41, 55, 0.3)",
            borderBottom: "1px solid #374151",
          }}
        >
          <div
            style={{
              maxWidth: "1280px",
              margin: "0 auto",
              padding: "12px 24px",
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <span
              style={{ color: "#ffffff", fontSize: "14px", fontWeight: "500" }}
            >
              📄 {selectedFile.name}
            </span>
            <span style={{ color: "#9ca3af", fontSize: "12px" }}>
              ({(selectedFile.size / 1024).toFixed(1)} KB)
              {supportsTrueRefresh &&
                fileHandle &&
                " • ⚡ Live refresh enabled"}
            </span>
            <span style={{ color: "#9ca3af", fontSize: "12px" }}>
              •{" "}
              {supportsTrueRefresh
                ? fileHandle
                  ? "Refresh loads latest data from disk"
                  : "File will auto-enable live refresh on Chrome/Edge"
                : "Viewing file snapshot (refresh not available on this browser)"}
            </span>
          </div>
        </div>
      )}

      {/* Stats Bar */}
      {logs.length > 0 && (
        <div
          style={{
            backgroundColor: "rgba(31, 41, 55, 0.3)",
            borderBottom: "1px solid #374151",
          }}
        >
          <div
            style={{
              maxWidth: "1280px",
              margin: "0 auto",
              padding: "16px 24px",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                backgroundColor: "rgba(31, 41, 55, 0.5)",
                padding: "16px",
                borderRadius: "8px",
                border: "1px solid #374151",
              }}
            >
              <DollarSign size={20} color="#fbbf24" />
              <div style={{ flex: 1 }}>
                <p
                  style={{
                    color: "#9ca3af",
                    fontSize: "14px",
                    margin: "0 0 4px 0",
                  }}
                >
                  Total Cost
                </p>
                <p
                  style={{
                    fontSize: "20px",
                    fontWeight: "600",
                    margin: 0,
                    color: "#fbbf24",
                  }}
                >
                  {formatCurrency(stats.totalCost)}
                </p>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                backgroundColor: "rgba(31, 41, 55, 0.5)",
                padding: "16px",
                borderRadius: "8px",
                border: "1px solid #374151",
              }}
            >
              <Zap size={20} color="#60a5fa" />
              <div style={{ flex: 1 }}>
                <p
                  style={{
                    color: "#9ca3af",
                    fontSize: "14px",
                    margin: "0 0 4px 0",
                  }}
                >
                  Total Tokens
                </p>
                <p
                  style={{
                    fontSize: "20px",
                    fontWeight: "600",
                    margin: 0,
                    color: "#60a5fa",
                  }}
                >
                  {stats.totalTokens.toLocaleString()}
                </p>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                backgroundColor: "rgba(31, 41, 55, 0.5)",
                padding: "16px",
                borderRadius: "8px",
                border: "1px solid #374151",
              }}
            >
              <Clock size={20} color="#a78bfa" />
              <div style={{ flex: 1 }}>
                <p
                  style={{
                    color: "#9ca3af",
                    fontSize: "14px",
                    margin: "0 0 4px 0",
                  }}
                >
                  Avg Duration
                </p>
                <p
                  style={{
                    fontSize: "20px",
                    fontWeight: "600",
                    margin: 0,
                    color: "#a78bfa",
                  }}
                >
                  {formatDuration(stats.avgDuration)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div style={{ display: "flex", height: "calc(100vh - 200px)" }}>
        {/* Sidebar - Sessions List */}
        {Object.entries(sessions).length > 0 && (
          <div
            style={{
              width: "350px",
              backgroundColor: "rgba(31, 41, 55, 0.3)",
              borderRight: "1px solid #374151",
              overflow: "auto",
              flexShrink: 0,
            }}
          >
            <div style={{ padding: "16px", borderBottom: "1px solid #374151" }}>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#ffffff",
                  margin: 0,
                }}
              >
                Sessions ({Object.keys(sessions).length})
              </h3>
            </div>

            <div>
              {Object.entries(sessions).map(([sessionId, sessionLogs]) => (
                <div
                  key={sessionId}
                  style={{
                    padding: "16px",
                    borderBottom: "1px solid #374151",
                    cursor: "pointer",
                    backgroundColor:
                      selectedSession === sessionId
                        ? "rgba(96, 165, 250, 0.1)"
                        : "transparent",
                    borderLeft:
                      selectedSession === sessionId
                        ? "3px solid #60a5fa"
                        : "3px solid transparent",
                    transition: "all 0.2s",
                  }}
                  onClick={() => setSelectedSession(sessionId)}
                  onMouseEnter={(e) => {
                    if (selectedSession !== sessionId) {
                      e.currentTarget.style.backgroundColor =
                        "rgba(31, 41, 55, 0.3)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedSession !== sessionId) {
                      e.currentTarget.style.backgroundColor = "transparent";
                    }
                  }}
                >
                  <div style={{ marginBottom: "8px" }}>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "#9ca3af",
                        fontFamily: "monospace",
                        marginBottom: "4px",
                        wordBreak: "break-all",
                      }}
                    >
                      {sessionId.substring(0, 20)}...
                    </div>

                    <div
                      style={{
                        fontSize: "14px",
                        color: "#f9fafb",
                        lineHeight: "1.4",
                        marginBottom: "8px",
                      }}
                    >
                      {getSessionPreview(sessionLogs)}
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "12px",
                        fontSize: "12px",
                        color: "#9ca3af",
                      }}
                    >
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <Activity size={12} />
                        {sessionLogs.length}
                      </span>
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <DollarSign size={12} />
                        {formatCurrency(
                          sessionLogs.reduce(
                            (sum, log) => sum + (log.cost_usd || 0),
                            0
                          )
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div style={{ flex: 1, overflow: "auto" }}>
          <div style={{ padding: "24px" }}>
            {isLoading ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: "200px",
                  gap: "12px",
                  fontSize: "16px",
                  color: "#9ca3af",
                }}
              >
                <RefreshCw
                  size={24}
                  style={{ animation: "spin 1s linear infinite" }}
                />
                Loading CSV data...
              </div>
            ) : selectedSession && sessions[selectedSession] ? (
              <div>
                {/* Session Header */}
                <div
                  style={{
                    backgroundColor: "rgba(31, 41, 55, 0.3)",
                    borderRadius: "12px",
                    border: "1px solid #374151",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      backgroundColor: "rgba(31, 41, 55, 0.5)",
                      padding: "16px 24px",
                      borderBottom: "1px solid #374151",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      flexWrap: "wrap",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <h3
                        style={{
                          fontSize: "18px",
                          fontWeight: "600",
                          color: "#ffffff",
                          margin: "0 0 4px 0",
                        }}
                      >
                        Session Details
                      </h3>
                      <p
                        style={{
                          fontSize: "12px",
                          color: "#9ca3af",
                          fontFamily: "monospace",
                          margin: 0,
                          wordBreak: "break-all",
                        }}
                      >
                        {selectedSession}
                      </p>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "16px",
                        fontSize: "14px",
                        flexWrap: "wrap",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          color: "#9ca3af",
                        }}
                      >
                        <Activity size={16} />
                        <span>{sessions[selectedSession].length} actions</span>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          color: "#9ca3af",
                        }}
                      >
                        <DollarSign size={16} />
                        <span>
                          {formatCurrency(
                            sessions[selectedSession].reduce(
                              (sum, log) => sum + (log.cost_usd || 0),
                              0
                            )
                          )}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Session Logs */}
                  <div>
                    {sessions[selectedSession].map((log) => (
                      <div
                        key={log.action_id}
                        style={{
                          padding: "24px",
                          borderBottom: "1px solid #374151",
                          display: "flex",
                          alignItems: "flex-start",
                          gap: "16px",
                          transition: "background-color 0.2s",
                          backgroundColor:
                            hoveredLog === log.action_id
                              ? "rgba(31, 41, 55, 0.3)"
                              : "transparent",
                        }}
                        onMouseEnter={() => setHoveredLog(log.action_id)}
                        onMouseLeave={() => setHoveredLog(null)}
                      >
                        {/* Action Icon */}
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: "40px",
                            height: "40px",
                            borderRadius: "8px",
                            border: "1px solid",
                            flexShrink: 0,
                            color:
                              log.action_type === "llm_call"
                                ? "#60a5fa"
                                : log.action_type === "tool_use"
                                ? "#34d399"
                                : "#a78bfa",
                            backgroundColor:
                              log.action_type === "llm_call"
                                ? "rgba(96, 165, 250, 0.1)"
                                : log.action_type === "tool_use"
                                ? "rgba(52, 211, 153, 0.1)"
                                : "rgba(167, 139, 250, 0.1)",
                            borderColor:
                              log.action_type === "llm_call"
                                ? "rgba(96, 165, 250, 0.2)"
                                : log.action_type === "tool_use"
                                ? "rgba(52, 211, 153, 0.2)"
                                : "rgba(167, 139, 250, 0.2)",
                          }}
                        >
                          {getActionIcon(log.action_type)}
                        </div>

                        {/* Content */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              marginBottom: "12px",
                              flexWrap: "wrap",
                              gap: "8px",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                flexWrap: "wrap",
                              }}
                            >
                              <span
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  padding: "4px 8px",
                                  borderRadius: "12px",
                                  fontSize: "12px",
                                  fontWeight: "500",
                                  border: "1px solid",
                                  color:
                                    log.action_type === "llm_call"
                                      ? "#60a5fa"
                                      : log.action_type === "tool_use"
                                      ? "#34d399"
                                      : "#9ca3af",
                                  backgroundColor:
                                    log.action_type === "llm_call"
                                      ? "rgba(96, 165, 250, 0.1)"
                                      : log.action_type === "tool_use"
                                      ? "rgba(52, 211, 153, 0.1)"
                                      : "#374151",
                                  borderColor:
                                    log.action_type === "llm_call"
                                      ? "rgba(96, 165, 250, 0.2)"
                                      : log.action_type === "tool_use"
                                      ? "rgba(52, 211, 153, 0.2)"
                                      : "#374151",
                                }}
                              >
                                {log.action_type}
                              </span>

                              {log.model_name && (
                                <span
                                  style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    padding: "4px 8px",
                                    borderRadius: "12px",
                                    fontSize: "12px",
                                    fontWeight: "500",
                                    border: "1px solid",
                                    color: "#9ca3af",
                                    backgroundColor: "#374151",
                                    borderColor: "#374151",
                                  }}
                                >
                                  {log.model_name}
                                </span>
                              )}
                            </div>

                            <div style={{ fontSize: "14px", color: "#9ca3af" }}>
                              {formatTimestamp(log.timestamp)}
                            </div>
                          </div>

                          {log.action_type === "llm_call" && (
                            <div style={{ marginBottom: "16px" }}>
                              <div style={{ marginBottom: "12px" }}>
                                <p
                                  style={{
                                    fontSize: "14px",
                                    fontWeight: "500",
                                    color: "#9ca3af",
                                    marginBottom: "4px",
                                  }}
                                >
                                  Input:
                                </p>
                                <div
                                  style={{
                                    fontSize: "14px",
                                    color: "#f9fafb",
                                    backgroundColor: "rgba(31, 41, 55, 0.5)",
                                    padding: "12px",
                                    borderRadius: "8px",
                                    border: "1px solid #374151",
                                    lineHeight: "1.5",
                                    wordBreak: "break-word",
                                  }}
                                >
                                  {renderStructuredInput(
                                    extractUserInput(log.input_data)
                                  )}
                                </div>
                              </div>

                              <div style={{ marginBottom: "12px" }}>
                                <p
                                  style={{
                                    fontSize: "14px",
                                    fontWeight: "500",
                                    color: "#9ca3af",
                                    marginBottom: "4px",
                                  }}
                                >
                                  Response:
                                </p>
                                <div
                                  style={{
                                    fontSize: "14px",
                                    color: "#f9fafb",
                                    backgroundColor: "rgba(31, 41, 55, 0.5)",
                                    padding: "12px",
                                    borderRadius: "8px",
                                    border: "1px solid #374151",
                                    lineHeight: "1.5",
                                    wordBreak: "break-word",
                                  }}
                                >
                                  {renderStructuredResponse(
                                    extractResponse(log.output_data)
                                  )}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Metrics */}
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "20px",
                              fontSize: "14px",
                              color: "#9ca3af",
                              flexWrap: "wrap",
                            }}
                          >
                            {log.total_tokens && (
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "4px",
                                }}
                              >
                                <Zap size={16} />
                                <span>
                                  {log.prompt_tokens}→{log.completion_tokens} (
                                  {log.total_tokens} total)
                                </span>
                              </div>
                            )}

                            {log.cost_usd && (
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "4px",
                                }}
                              >
                                <DollarSign size={16} />
                                <span>{formatCurrency(log.cost_usd)}</span>
                              </div>
                            )}

                            {log.duration_ms && (
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "4px",
                                }}
                              >
                                <Clock size={16} />
                                <span>{formatDuration(log.duration_ms)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : Object.entries(sessions).length === 0 ? (
              <div style={{ textAlign: "center", padding: "60px 20px" }}>
                <Upload
                  size={48}
                  color="#6b7280"
                  style={{ margin: "0 auto 16px" }}
                />
                <h3
                  style={{
                    fontSize: "18px",
                    fontWeight: "500",
                    color: "#9ca3af",
                    margin: "16px 0 8px 0",
                  }}
                >
                  No CSV file selected
                </h3>
                <p style={{ color: "#6b7280", margin: 0 }}>
                  Click "Select CSV File" above to load your agent breadcrumbs
                </p>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "60px 20px" }}>
                <h3
                  style={{
                    fontSize: "18px",
                    fontWeight: "500",
                    color: "#9ca3af",
                    margin: "16px 0 8px 0",
                  }}
                >
                  Select a session
                </h3>
                <p style={{ color: "#6b7280", margin: 0 }}>
                  Choose a session from the sidebar to view its details
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default BreadcrumbsDashboard;

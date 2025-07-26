import React, { useState, useEffect } from "react";
import { Clock, Zap, DollarSign, MessageSquare, Wrench, Activity, RefreshCw, Upload } from "./components/Icons";
import { extractUserInput, renderStructuredInput, extractResponse, renderStructuredResponse } from "./utils/parseUtils";
import { formatTimestamp, formatCurrency, formatDuration, getActionIcon, getTotalStats, getSessionPreview } from "./utils/statsUtils";
import { LogEntry } from "./utils/csvReader";
import "./BreadcrumbsDashboard.css";


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
  // Auto-select first session when sessions load
  useEffect(() => {
    const sessionIds = Object.keys(sessions);
    if (sessionIds.length > 0 && !selectedSession) {
      setSelectedSession(sessionIds[0]);
    }
  }, [sessions, selectedSession]);

  const stats = getTotalStats(logs);

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

    </div>
  );
};

export default BreadcrumbsDashboard;

import React, { useState, useEffect } from "react";
import {
  Clock,
  Zap,
  DollarSign,
  MessageSquare,
  Wrench,
  Activity,
  RefreshCw,
} from "lucide-react";

// Types
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

// Simple CSV reader function
const readCSVFile = async (filePath: string): Promise<LogEntry[]> => {
  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const csvText = await response.text();

    const lines = csvText.split("\n").filter((line) => line.trim());
    if (lines.length === 0) return [];

    const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""));

    const logs: LogEntry[] = lines.slice(1).map((line) => {
      const values = [] as any;
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
        const value = values[index] || "";

        switch (header) {
          case "prompt_tokens":
          case "completion_tokens":
          case "total_tokens":
            logEntry[header] = value ? parseInt(value) : null;
            break;
          case "cost_usd":
          case "duration_ms":
            logEntry[header] = value ? parseFloat(value) : null;
            break;
          default:
            logEntry[header] = value.replace(/^"|"$/g, "");
        }
      });

      return logEntry as LogEntry;
    });

    return logs.filter((log) => log.action_id);
  } catch (error) {
    console.error("Error reading CSV file:", error);

    // Return mock data
    return [
      {
        action_id: "mock-1",
        session_id: "mock-session-1",
        timestamp: new Date().toISOString(),
        action_type: "llm_call",
        input_data: JSON.stringify({
          prompt:
            "System: You are a weather assistant.\nHuman: What's the weather in San Francisco?",
        }),
        output_data: JSON.stringify({
          response: "🔧 Decided to call tool: get_weather(city=San Francisco)",
        }),
        model_name: "gpt-4o-mini",
        prompt_tokens: 45,
        completion_tokens: 12,
        total_tokens: 57,
        cost_usd: 0.000025,
        duration_ms: 738,
        metadata: JSON.stringify({ langchain_integration: true }),
      },
      {
        action_id: "mock-2",
        session_id: "mock-session-1",
        timestamp: new Date().toISOString(),
        action_type: "llm_call",
        input_data: JSON.stringify({
          prompt:
            "System: You are a weather assistant.\nHuman: What's the weather in San Francisco?\nAI: \nTool: Sunny, 72°F",
        }),
        output_data: JSON.stringify({
          response:
            "The weather in San Francisco is sunny with a temperature of 72°F.",
        }),
        model_name: "gpt-4o-mini",
        prompt_tokens: 52,
        completion_tokens: 18,
        total_tokens: 70,
        cost_usd: 0.000032,
        duration_ms: 482,
        metadata: JSON.stringify({ langchain_integration: true }),
      },
      {
        action_id: "mock-3",
        session_id: "mock-session-2",
        timestamp: new Date().toISOString(),
        action_type: "llm_call",
        input_data: JSON.stringify({
          prompt: "System: You are a calculator.\nHuman: What is 25 + 17?",
        }),
        output_data: JSON.stringify({
          response: "🔧 Decided to call tool: add(a=25, b=17)",
        }),
        model_name: "gpt-4o-mini",
        prompt_tokens: 38,
        completion_tokens: 14,
        total_tokens: 52,
        cost_usd: 0.000021,
        duration_ms: 661,
        metadata: JSON.stringify({ langchain_integration: true }),
      },
    ];
  }
};

// CSS Styles
const styles = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#111827",
    color: "#f9fafb",
  },

  header: {
    borderBottom: "1px solid #374151",
    backgroundColor: "rgba(31, 41, 55, 0.5)",
    backdropFilter: "blur(12px)",
    position: "sticky" as const,
    top: 0,
    zIndex: 10,
  },

  headerContent: {
    maxWidth: "1280px",
    margin: "0 auto",
    padding: "16px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap" as const,
    gap: "16px",
  },

  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },

  headerTitle: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#ffffff",
    margin: 0,
  },

  headerSubtitle: {
    color: "#9ca3af",
    fontSize: "14px",
    margin: 0,
  },

  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "24px",
    flexWrap: "wrap" as const,
  },

  lastUpdated: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "14px",
    color: "#9ca3af",
  },

  headerStats: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },

  headerStatCard: {
    backgroundColor: "#1f2937",
    padding: "8px 12px",
    borderRadius: "8px",
    border: "1px solid #374151",
    textAlign: "center" as const,
    minWidth: "70px",
  },

  headerStatLabel: {
    color: "#9ca3af",
    fontSize: "12px",
    display: "block",
    marginBottom: "2px",
  },

  headerStatValue: {
    fontSize: "18px",
    fontWeight: "600",
    margin: 0,
  },

  statsBar: {
    backgroundColor: "rgba(31, 41, 55, 0.3)",
    borderBottom: "1px solid #374151",
  },

  statsContent: {
    maxWidth: "1280px",
    margin: "0 auto",
    padding: "16px 24px",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "16px",
  },

  statCard: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    backgroundColor: "rgba(31, 41, 55, 0.5)",
    padding: "16px",
    borderRadius: "8px",
    border: "1px solid #374151",
  },

  statContent: {
    flex: 1,
  },

  statLabel: {
    color: "#9ca3af",
    fontSize: "14px",
    margin: "0 0 4px 0",
  },

  statValue: {
    fontSize: "20px",
    fontWeight: "600",
    margin: 0,
  },

  mainContent: {
    maxWidth: "1280px",
    margin: "0 auto",
    padding: "24px",
  },

  sessionCard: {
    backgroundColor: "rgba(31, 41, 55, 0.3)",
    borderRadius: "12px",
    border: "1px solid #374151",
    overflow: "hidden",
    marginBottom: "24px",
  },

  sessionHeader: {
    backgroundColor: "rgba(31, 41, 55, 0.5)",
    padding: "16px 24px",
    borderBottom: "1px solid #374151",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap" as const,
    gap: "12px",
  },

  sessionTitle: {
    fontSize: "18px",
    fontWeight: "600",
    color: "#ffffff",
    margin: "0 0 4px 0",
  },

  sessionId: {
    fontSize: "12px",
    color: "#9ca3af",
    fontFamily: "monospace",
    margin: 0,
    wordBreak: "break-all" as const,
  },

  sessionStats: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    fontSize: "14px",
    flexWrap: "wrap" as const,
  },

  sessionStat: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: "#9ca3af",
  },

  logItem: {
    padding: "24px",
    borderBottom: "1px solid #374151",
    display: "flex",
    alignItems: "flex-start",
    gap: "16px",
    transition: "background-color 0.2s",
    cursor: "default",
  },

  logIcon: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "40px",
    height: "40px",
    borderRadius: "8px",
    border: "1px solid",
    flexShrink: 0,
  },

  logContent: {
    flex: 1,
    minWidth: 0,
  },

  logHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "12px",
    flexWrap: "wrap" as const,
    gap: "8px",
  },

  logBadges: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap" as const,
  },

  badge: {
    display: "inline-flex",
    alignItems: "center",
    padding: "4px 8px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "500",
    border: "1px solid",
  },

  timestamp: {
    fontSize: "14px",
    color: "#9ca3af",
  },

  logDetails: {
    marginBottom: "16px",
  },

  logSection: {
    marginBottom: "12px",
  },

  logLabel: {
    fontSize: "14px",
    fontWeight: "500",
    color: "#9ca3af",
    marginBottom: "4px",
  },

  logText: {
    fontSize: "14px",
    color: "#f9fafb",
    backgroundColor: "rgba(31, 41, 55, 0.5)",
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #374151",
    lineHeight: "1.5",
    wordBreak: "break-word" as const,
  },

  logMetrics: {
    display: "flex",
    alignItems: "center",
    gap: "20px",
    fontSize: "14px",
    color: "#9ca3af",
    flexWrap: "wrap" as const,
  },

  metric: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },

  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    gap: "12px",
    fontSize: "18px",
    color: "#9ca3af",
  },

  emptyState: {
    textAlign: "center" as const,
    padding: "60px 20px",
  },

  emptyTitle: {
    fontSize: "18px",
    fontWeight: "500",
    color: "#9ca3af",
    margin: "16px 0 8px 0",
  },

  emptyText: {
    color: "#6b7280",
    margin: 0,
  },

  error: {
    backgroundColor: "#7f1d1d",
    border: "1px solid #dc2626",
    borderRadius: "8px",
    padding: "16px",
    color: "#fecaca",
    margin: "24px",
  },
};

const BreadcrumbsDashboard = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [sessions, setSessions] = useState<{ [key: string]: LogEntry[] }>({});
  const [hoveredLog, setHoveredLog] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const csvLogs = await readCSVFile("/agent_logs.csv");
        setLogs(csvLogs);
        setLastUpdated(new Date());

        // Group by sessions
        const sessionGroups = csvLogs.reduce((acc, log) => {
          if (!acc[log.session_id]) {
            acc[log.session_id] = [];
          }
          acc[log.session_id].push(log);
          return acc;
        }, {} as { [key: string]: LogEntry[] });

        setSessions(sessionGroups);
      } catch (error) {
        console.error("Error loading data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

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

  const getActionIconStyle = (actionType: string) => {
    switch (actionType) {
      case "llm_call":
        return {
          ...styles.logIcon,
          color: "#60a5fa",
          backgroundColor: "rgba(96, 165, 250, 0.1)",
          borderColor: "rgba(96, 165, 250, 0.2)",
        };
      case "tool_use":
        return {
          ...styles.logIcon,
          color: "#34d399",
          backgroundColor: "rgba(52, 211, 153, 0.1)",
          borderColor: "rgba(52, 211, 153, 0.2)",
        };
      default:
        return {
          ...styles.logIcon,
          color: "#a78bfa",
          backgroundColor: "rgba(167, 139, 250, 0.1)",
          borderColor: "rgba(167, 139, 250, 0.2)",
        };
    }
  };

  const getBadgeStyle = (actionType: string) => {
    switch (actionType) {
      case "llm_call":
        return {
          ...styles.badge,
          color: "#60a5fa",
          backgroundColor: "rgba(96, 165, 250, 0.1)",
          borderColor: "rgba(96, 165, 250, 0.2)",
        };
      case "tool_use":
        return {
          ...styles.badge,
          color: "#34d399",
          backgroundColor: "rgba(52, 211, 153, 0.1)",
          borderColor: "rgba(52, 211, 153, 0.2)",
        };
      default:
        return {
          ...styles.badge,
          color: "#9ca3af",
          backgroundColor: "#374151",
          borderColor: "#374151",
        };
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
    const parsed = parseJsonSafely(inputData);
    const prompt = parsed.prompt || "";

    const humanMatch = prompt.match(/Human: (.+?)(?=\n|$)/);
    return humanMatch ? humanMatch[1] : "Unknown input";
  };

  const extractResponse = (outputData: string) => {
    const parsed = parseJsonSafely(outputData);
    return parsed.response || "No response";
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

  const stats = getTotalStats();

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <RefreshCw
            size={24}
            style={{ animation: "spin 1s linear infinite" }}
          />
          Loading breadcrumbs...
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.headerLeft}>
            <Activity size={32} color="#60a5fa" />
            <div>
              <h1 style={styles.headerTitle}>Agent Breadcrumbs</h1>
              <p style={styles.headerSubtitle}>Real-time LLM observability</p>
            </div>
          </div>

          <div style={styles.headerRight}>
            <div style={styles.lastUpdated}>
              <RefreshCw size={16} />
              <span>
                Last updated: {lastUpdated?.toLocaleTimeString() || "Never"}
              </span>
            </div>

            <div style={styles.headerStats}>
              <div
                style={{
                  ...styles.headerStatCard,
                  ...styles.headerStatValue,
                  color: "#60a5fa",
                }}
              >
                <span style={styles.headerStatLabel}>Sessions</span>
                <div>{Object.keys(sessions).length}</div>
              </div>
              <div
                style={{
                  ...styles.headerStatCard,
                  ...styles.headerStatValue,
                  color: "#34d399",
                }}
              >
                <span style={styles.headerStatLabel}>Total Logs</span>
                <div>{logs.length}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div style={styles.statsBar}>
        <div style={styles.statsContent}>
          <div style={styles.statCard}>
            <DollarSign size={20} color="#fbbf24" />
            <div style={styles.statContent}>
              <p style={styles.statLabel}>Total Cost</p>
              <p style={{ ...styles.statValue, color: "#fbbf24" }}>
                {formatCurrency(stats.totalCost)}
              </p>
            </div>
          </div>

          <div style={styles.statCard}>
            <Zap size={20} color="#60a5fa" />
            <div style={styles.statContent}>
              <p style={styles.statLabel}>Total Tokens</p>
              <p style={{ ...styles.statValue, color: "#60a5fa" }}>
                {stats.totalTokens.toLocaleString()}
              </p>
            </div>
          </div>

          <div style={styles.statCard}>
            <Clock size={20} color="#a78bfa" />
            <div style={styles.statContent}>
              <p style={styles.statLabel}>Avg Duration</p>
              <p style={{ ...styles.statValue, color: "#a78bfa" }}>
                {formatDuration(stats.avgDuration)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {Object.entries(sessions).length > 0 ? (
          <div>
            {Object.entries(sessions).map(([sessionId, sessionLogs]) => (
              <div key={sessionId} style={styles.sessionCard}>
                {/* Session Header */}
                <div style={styles.sessionHeader}>
                  <div>
                    <h3 style={styles.sessionTitle}>Session</h3>
                    <p style={styles.sessionId}>{sessionId}</p>
                  </div>

                  <div style={styles.sessionStats}>
                    <div style={styles.sessionStat}>
                      <Activity size={16} />
                      <span>{sessionLogs.length} actions</span>
                    </div>

                    <div style={styles.sessionStat}>
                      <DollarSign size={16} />
                      <span>
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

                {/* Session Logs */}
                <div>
                  {sessionLogs.map((log) => (
                    <div
                      key={log.action_id}
                      style={{
                        ...styles.logItem,
                        backgroundColor:
                          hoveredLog === log.action_id
                            ? "rgba(31, 41, 55, 0.3)"
                            : "transparent",
                      }}
                      onMouseEnter={() => setHoveredLog(log.action_id)}
                      onMouseLeave={() => setHoveredLog(null)}
                    >
                      {/* Action Icon */}
                      <div style={getActionIconStyle(log.action_type)}>
                        {getActionIcon(log.action_type)}
                      </div>

                      {/* Content */}
                      <div style={styles.logContent}>
                        <div style={styles.logHeader}>
                          <div style={styles.logBadges}>
                            <span style={getBadgeStyle(log.action_type)}>
                              {log.action_type}
                            </span>

                            {log.model_name && (
                              <span
                                style={{
                                  ...styles.badge,
                                  ...getBadgeStyle("model"),
                                }}
                              >
                                {log.model_name}
                              </span>
                            )}
                          </div>

                          <div style={styles.timestamp}>
                            {formatTimestamp(log.timestamp)}
                          </div>
                        </div>

                        {/* Input/Output */}
                        {log.action_type === "llm_call" && (
                          <div style={styles.logDetails}>
                            <div style={styles.logSection}>
                              <p style={styles.logLabel}>Input:</p>
                              <p style={styles.logText}>
                                {extractUserInput(log.input_data)}
                              </p>
                            </div>

                            <div style={styles.logSection}>
                              <p style={styles.logLabel}>Response:</p>
                              <p style={styles.logText}>
                                {extractResponse(log.output_data)}
                              </p>
                            </div>
                          </div>
                        )}

                        {/* Metrics */}
                        <div style={styles.logMetrics}>
                          {log.total_tokens && (
                            <div style={styles.metric}>
                              <Zap size={16} />
                              <span>
                                {log.prompt_tokens}→{log.completion_tokens} (
                                {log.total_tokens} total)
                              </span>
                            </div>
                          )}

                          {log.cost_usd && (
                            <div style={styles.metric}>
                              <DollarSign size={16} />
                              <span>{formatCurrency(log.cost_usd)}</span>
                            </div>
                          )}

                          {log.duration_ms && (
                            <div style={styles.metric}>
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
            ))}
          </div>
        ) : (
          <div style={styles.emptyState}>
            <Activity
              size={48}
              color="#6b7280"
              style={{ margin: "0 auto 16px" }}
            />
            <h3 style={styles.emptyTitle}>No breadcrumbs yet</h3>
            <p style={styles.emptyText}>
              Start using your agent to see logs appear here
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BreadcrumbsDashboard;

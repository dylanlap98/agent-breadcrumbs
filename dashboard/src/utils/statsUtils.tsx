import { MessageSquare, Wrench, Activity } from "../components/Icons";
import type { LogEntry } from "./csvReader";

export const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};

export const formatCurrency = (amount: number | null) => {
  return amount ? `$${amount.toFixed(6)}` : "N/A";
};

export const formatDuration = (ms: number | null) => {
  return ms ? `${ms.toFixed(0)}ms` : "N/A";
};

export const getActionIcon = (actionType: string) => {
  switch (actionType) {
    case "llm_call":
      return <MessageSquare size={16} />;
    case "tool_use":
      return <Wrench size={16} />;
    default:
      return <Activity size={16} />;
  }
};

export const getTotalStats = (logs: LogEntry[]) => {
  const totalCost = logs.reduce((sum, log) => sum + (log.cost_usd || 0), 0);
  const totalTokens = logs.reduce((sum, log) => sum + (log.total_tokens || 0), 0);
  const avgDuration =
    logs.length > 0
      ? logs.reduce((sum, log) => sum + (log.duration_ms || 0), 0) / logs.length
      : 0;
  return { totalCost, totalTokens, avgDuration };
};

export const getSessionPreview = (
  sessionLogs: LogEntry[],
  extractUserInput: (data: string) => unknown
) => {
  const firstLlmCall = sessionLogs.find((log) => log.action_type === "llm_call");
  if (firstLlmCall) {
    const userInputData = extractUserInput(firstLlmCall.input_data) as
      | string
      | Record<string, unknown>;
    const promptText =
      typeof userInputData === "string"
        ? userInputData
        : (userInputData.prompt as string | undefined) || "Unknown input";
    return promptText.length > 60
      ? promptText.substring(0, 60) + "..."
      : promptText;
  }
  return "No user input found";
};

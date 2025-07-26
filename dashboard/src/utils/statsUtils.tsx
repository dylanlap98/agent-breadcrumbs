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
  const totalTokens = logs.reduce(
    (sum, log) => sum + (log.total_tokens || 0),
    0
  );
  const avgDuration =
    logs.length > 0
      ? logs.reduce((sum, log) => sum + (log.duration_ms || 0), 0) / logs.length
      : 0;
  return { totalCost, totalTokens, avgDuration };
};

export const getSessionPreview = (
  sessionLogs: LogEntry[],
  extractUserInput: (data: string) => Record<string, unknown>
) => {
  const firstLlmCall = sessionLogs.find(
    (log) => log.action_type === "llm_call"
  );
  if (firstLlmCall) {
    try {
      const userInputData = extractUserInput(firstLlmCall.input_data);

      let promptText = "Unknown input";

      if (typeof userInputData === "string") {
        promptText = userInputData;
      } else if (userInputData && typeof userInputData === "object") {
        const prompt = userInputData.prompt as string;
        if (prompt && typeof prompt === "string") {
          promptText = prompt;
        } else if (userInputData.content as string) {
          promptText = userInputData.content as string;
        } else if (userInputData.message as string) {
          promptText = userInputData.message as string;
        }
      }
      if (promptText && promptText !== "Unknown input") {
        promptText = promptText
          .replace(/\\n/g, " ")
          .replace(/\\"/g, '"')
          .trim();

        const maxLength = 60;
        if (promptText.length > maxLength) {
          promptText = promptText.substring(0, maxLength) + "...";
        }

        return promptText;
      }
    } catch (error) {
      console.warn("Error extracting session preview:", error);
    }
  }

  return "No user input found";
};

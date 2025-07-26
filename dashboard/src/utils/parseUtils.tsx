export const parseJsonSafely = (jsonString: string) => {
  try {
    return JSON.parse(jsonString);
  } catch {
    return {};
  }
};

export const extractUserInput = (inputData: string): Record<string, unknown> => {
  try {
    const parsed = JSON.parse(inputData);
    if (parsed.prompt) {
      return parsed;
    }
  } catch {
    try {
      const fixedJson = inputData
        .replace(/\{(\w+):/g, '{"$1":')
        .replace(/,\s*(\w+):/g, ', "$1":')
        .replace(/:\s*([^,[\]{}]+)(?=[,}])/g, ': "$1"')
        .replace(/:\s*(\[[^\]]+\])/g, ": $1");

      const parsed = JSON.parse(fixedJson);
      return parsed;
    } catch {
      const result: { [key: string]: unknown; prompt: string } = {
        prompt: "Unknown input",
      };
      const promptMatch = inputData.match(/prompt:\s*([^,}]+)/);
      if (promptMatch) result.prompt = promptMatch[1].trim();
      const toolMatch = inputData.match(/tool_responses:\s*\[([^\]]+)\]/);
      if (toolMatch) {
        result.tool_responses = toolMatch[1].split(",").map((v) => v.trim());
      }
      return result;
    }
  }
  return { prompt: inputData || "Unknown input" };
};

export const renderStructuredInput = (inputData: Record<string, unknown> | string) => {
  if (typeof inputData === "string") return inputData;

  if (typeof inputData === "object" && inputData !== null) {
    const data = inputData as Record<string, unknown>;
    const getFieldColor = (fieldName: string) => {
      const colorMap: Record<string, string> = {
        system: "#a78bfa",
        human: "#60a5fa",
        user: "#60a5fa",
        prompt: "#60a5fa",
        ai: "#34d399",
        assistant: "#34d399",
        tool: "#fbbf24",
        tool_responses: "#34d399",
        tool_results: "#34d399",
      };
      return colorMap[fieldName.toLowerCase()] || "#9ca3af";
    };

    const cleanText = (text: string) =>
      text.replace(/\\u([0-9a-fA-F]{4})/g, (_, code) =>
        String.fromCharCode(parseInt(code, 16))
      );

    const specialFields = ["tool_responses", "tool_results"];
    const regularFields = Object.keys(data).filter(
      (key) => !specialFields.includes(key)
    );
    const toolResponses = data.tool_responses as unknown as string[] | undefined;
    const toolResults = data.tool_results as unknown as string[] | undefined;

    return (
      <div>
        {regularFields.map((fieldName) => {
          const record = data as Record<string, unknown>;
          const value = record[fieldName];
          if (!value || (typeof value === "string" && value.trim() === "")) {
            return null;
          }
          const displayValue =
            typeof value === "string" ? cleanText(value) : JSON.stringify(value);
          return (
            <div key={fieldName} style={{ marginBottom: "8px" }}>
              <span style={{ fontWeight: "600", color: getFieldColor(fieldName) }}>
                {fieldName}
              </span>
              <span style={{ color: "#9ca3af" }}>: </span>
              <span>{displayValue}</span>
            </div>
          );
        })}
        {(toolResponses || toolResults) && (
          <div>
            <span style={{ fontWeight: "600", color: "#34d399" }}>
              {toolResponses ? "tool responses" : "tool results"}
            </span>
            <span style={{ color: "#9ca3af" }}>: </span>
            <span style={{ color: "#fbbf24" }}>
              [
              {(toolResponses || toolResults)?.join(
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

const parseToolCalls = (response: string) => {
  const toolPattern = /🔧\s*Decided to call tools?:\s*(.+)/;
  const match = response.match(toolPattern);
  if (match) {
    const toolsText = match[1];
    const toolCalls = toolsText.split(/,\s*(?=[a-zA-Z_][a-zA-Z0-9_]*\()/);
    return { hasTools: true, tools: toolCalls.map((t) => t.trim()), originalResponse: response };
  }
  return { hasTools: false, tools: [], originalResponse: response };
};

export const extractResponse = (outputData: string) => {
  try {
    const parsed = JSON.parse(outputData);
    if (parsed.response) {
      return { response: parsed.response };
    }
    return parsed;
  } catch {
    try {
      const fixedJson = outputData
        .replace(/\{(\w+):/g, '{"$1":')
        .replace(/,\s*(\w+):/g, ', "$1":')
        .replace(/:\s*([^,[\]{}]+)(?=[,}])/g, ': "$1"')
        .replace(/:\s*(\[[^\]]+\])/g, ": $1");
      const parsed = JSON.parse(fixedJson);
      if (parsed.response) {
        let cleanResponse = parsed.response;
        cleanResponse = cleanResponse.replace(
          /\\\\u([0-9a-fA-F]{4})/g,
          (_: string, c: string) => String.fromCharCode(parseInt(c, 16))
        );
        cleanResponse = cleanResponse.replace(
          /\\u([0-9a-fA-F]{4})/g,
          (_: string, c: string) => String.fromCharCode(parseInt(c, 16))
        );
        cleanResponse = cleanResponse.replace(/\\\\/g, "\\");
        return { response: cleanResponse };
      }
      return parsed;
      } catch {
        const result: { [key: string]: unknown; response: string } = {
          response: "Unknown response",
        };
      const responseMatch = outputData.match(/response:\s*(.+)$/);
      if (responseMatch) {
        let response = responseMatch[1].trim();
        response = response.replace(/\\u([0-9a-fA-F]{4})/g, (_, code) =>
          String.fromCharCode(parseInt(code, 16))
        );
        result.response = response;
      }
      return result;
    }
  }
};

export const renderStructuredResponse = (
  responseData: Record<string, unknown> | string
) => {
  if (typeof responseData === "string") {
    const toolInfo = parseToolCalls(responseData);
    if (toolInfo.hasTools) {
      return (
        <div>
          <div style={{ marginBottom: "8px", color: "#fbbf24" }}>🔧 Tool calls:</div>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "#34d399" }}>
            {toolInfo.tools.map((tool: string, i: number) => (
              <li key={i} style={{ marginBottom: "4px" }}>
                <code style={{ backgroundColor: "rgba(52, 211, 153, 0.1)", padding: "2px 6px", borderRadius: "4px", fontFamily: "monospace", fontSize: "13px" }}>
                  {tool}
                </code>
              </li>
            ))}
          </ul>
        </div>
      );
    }
    return responseData;
  }

  if ((responseData as Record<string, unknown>).response) {
    const respObj = responseData as Record<string, unknown>;
    const responseText = String(respObj.response);
    const toolInfo = parseToolCalls(responseText);
    if (toolInfo.hasTools) {
      return (
        <div>
          <div style={{ marginBottom: "8px", color: "#fbbf24" }}>🔧 Tool calls:</div>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "#34d399" }}>
            {toolInfo.tools.map((tool: string, i: number) => (
              <li key={i} style={{ marginBottom: "4px" }}>
                <code style={{ backgroundColor: "rgba(52, 211, 153, 0.1)", padding: "2px 6px", borderRadius: "4px", fontFamily: "monospace", fontSize: "13px" }}>
                  {tool}
                </code>
              </li>
            ))}
          </ul>
        </div>
      );
    }
    return (
      <div>
        <span style={{ fontWeight: "600", color: "#60a5fa" }}>response</span>
        <span style={{ color: "#9ca3af" }}>: </span>
        <span>{responseText}</span>
      </div>
    );
  }
  return JSON.stringify(responseData);
};

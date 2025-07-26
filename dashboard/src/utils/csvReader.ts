export interface LogEntry {
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
  
  export const readCSVFile = async (filePath: string): Promise<LogEntry[]> => {
    try {
      const response = await fetch(filePath);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const csvText = await response.text();
      
      // Simple CSV parsing
      const lines = csvText.split('\n').filter(line => line.trim());
      if (lines.length === 0) return [];
      
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      
      const logs: LogEntry[] = lines.slice(1).map(line => {
        // Handle CSV with quotes and commas
        const values: string[] = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
          const char = line[i];
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
          } else {
            current += char;
          }
        }
        values.push(current.trim()); // Don't forget the last value
        
        const logEntry: Partial<LogEntry> = {};
        const entry = logEntry as Record<string, string | number | null>;
        headers.forEach((header, index) => {
          const value = values[index] ?? '';
          
          // Parse specific fields
          switch (header) {
            case 'prompt_tokens':
            case 'completion_tokens':
            case 'total_tokens':
              entry[header] = value ? parseInt(value) : null;
              break;
            case 'cost_usd':
            case 'duration_ms':
              entry[header] = value ? parseFloat(value) : null;
              break;
            default:
              entry[header] = value.replace(/^"|"$/g, ''); // Remove surrounding quotes
          }
        });
        
        return logEntry as LogEntry;
      });
      
      return logs.filter(log => log.action_id); // Filter out empty rows
      
    } catch (error) {
      console.error('Error reading CSV file:', error);
      
      // Return mock data if file can't be read
      return [
        {
          action_id: "mock-1",
          session_id: "mock-session",
          timestamp: new Date().toISOString(),
          action_type: "llm_call",
          input_data: JSON.stringify({prompt: "Mock: What is 2+2?"}),
          output_data: JSON.stringify({response: "🔧 Decided to call tool: calculator(expression=2+2)"}),
          model_name: "gpt-4o-mini",
          prompt_tokens: 15,
          completion_tokens: 8,
          total_tokens: 23,
          cost_usd: 0.000012,
          duration_ms: 450,
          metadata: JSON.stringify({mock: true})
        },
        {
          action_id: "mock-2",
          session_id: "mock-session",
          timestamp: new Date().toISOString(),
          action_type: "llm_call",
          input_data: JSON.stringify({prompt: "Mock: Tool result: 4"}),
          output_data: JSON.stringify({response: "The answer is 4."}),
          model_name: "gpt-4o-mini",
          prompt_tokens: 20,
          completion_tokens: 6,
          total_tokens: 26,
          cost_usd: 0.000008,
          duration_ms: 320,
          metadata: JSON.stringify({mock: true})
        }
      ];
    }
  };
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ChatResponse {
  response: string;
  risk_profile?: Record<string, any>;
  thread_id: string;
}

export const apiService = {
  /**
   * Sends a message to the RAG assistant and returns the grounded response and risk profile.
   */
  async chat(message: string, thread_id?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message, thread_id }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();
      return data;
    } catch (error) {
      console.error("Failed to fetch chat response:", error);
      throw error;
    }
  },

  /**
   * Checks backend health.
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
};

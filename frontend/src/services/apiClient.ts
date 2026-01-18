import axios, { AxiosInstance, AxiosError } from "axios";

// API base URL - can be configured via environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Token storage key
const TOKEN_KEY = "auth_token";

interface LoginResponse {
  token: string;
  token_type: string;
}

interface RegisterResponse {
  message: string;
  user_id: string;
}

interface QueryResponse {
  answer: string;
  sources?: any[];
  answer_type?: string;
  drawing_context_used?: boolean;
  knowledge_summary?: {
    overview: string;
    topics: string[];
    suggested_questions: string[];
  };
}

interface UpdateObjectListResponse {
  message: string;
}

class ApiClient {
  private client: AxiosInstance;
  private onUnauthorized?: () => void;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add request interceptor to include token in headers
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      },
    );

    // Add response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Only trigger unauthorized callback if user was actually logged in
          const hadToken = this.getToken() !== null;

          // Token expired or invalid - clear it
          this.clearToken();

          // Call the unauthorized callback only if user was logged in
          // (don't show "session expired" on login page)
          if (hadToken && this.onUnauthorized) {
            this.onUnauthorized();
          }
        }
        return Promise.reject(this.handleError(error));
      },
    );
  }

  // Set callback for unauthorized responses (token expiration)
  public setUnauthorizedCallback(callback: () => void): void {
    this.onUnauthorized = callback;
  }

  private handleError(error: AxiosError): Error {
    if (error.response?.data) {
      const data = error.response.data as any;
      if (data.detail) {
        return new Error(data.detail);
      }
      if (data.error?.message) {
        return new Error(data.error.message);
      }
    }
    return new Error(error.message || "An unexpected error occurred");
  }

  // Token management
  private getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  private setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  private clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  public isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  // Authentication methods
  async login(username: string, password: string): Promise<string> {
    try {
      const response = await this.client.post<LoginResponse>(
        "/api/auth/login",
        {
          username,
          password,
        },
      );

      const token = response.data.token;
      this.setToken(token);
      return token;
    } catch (error) {
      throw error;
    }
  }

  async register(
    username: string,
    password: string,
  ): Promise<RegisterResponse> {
    try {
      const response = await this.client.post<RegisterResponse>(
        "/api/auth/register",
        {
          username,
          password,
        },
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  logout(): void {
    this.clearToken();
  }

  // Session management methods
  async updateObjectList(objects: any[]): Promise<UpdateObjectListResponse> {
    try {
      const response = await this.client.post<UpdateObjectListResponse>(
        "/api/session/objects",
        { objects },
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getObjectList(): Promise<{
    objects: any[];
    created_at?: string;
    updated_at?: string;
  }> {
    try {
      const response = await this.client.get<{
        objects: any[];
        created_at?: string;
        updated_at?: string;
      }>("/api/session/objects");
      return {
        objects: response.data.objects || [],
        created_at: response.data.created_at,
        updated_at: response.data.updated_at,
      };
    } catch (error) {
      throw error;
    }
  }

  // Query methods
  async query(question: string): Promise<QueryResponse> {
    try {
      const response = await this.client.post<QueryResponse>("/api/query", {
        question,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Agentic query method (multi-step reasoning)
  async queryAgentic(question: string): Promise<QueryResponse> {
    try {
      const response = await this.client.post<QueryResponse>(
        "/api/query-agentic",
        {
          question,
        },
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Knowledge summary methods
  async getKnowledgeSummary(): Promise<{
    overview: string;
    topics: string[];
    suggested_questions: string[];
  }> {
    try {
      const response = await this.client.get("/api/knowledge-summary");
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

// Export a singleton instance
const apiClient = new ApiClient();
export default apiClient;

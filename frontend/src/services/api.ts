import axios from 'axios';
import type {
  ChatResponse,
  DatasetPreview,
  DatasetProfile,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /** Uploads CSV file with multipart form-data */
  async uploadCSV(file: File): Promise<DatasetProfile> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<DatasetProfile>('/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /** Fetches dataset profiling metadata */
  async getProfile(datasetId: string): Promise<DatasetProfile> {
    const response = await apiClient.get<DatasetProfile>(`/datasets/${datasetId}/profile`);
    return response.data;
  },

  /** Retrieves first N rows of dataset */
  async getPreview(datasetId: string, limit: number = 15): Promise<DatasetPreview> {
    const response = await apiClient.get<DatasetPreview>(`/datasets/${datasetId}/preview`, {
      params: { limit },
    });
    return response.data;
  },

  /** Updates or confirms semantic column mappings */
  async updateMappings(
    datasetId: string,
    mappings: Record<string, string>
  ): Promise<{ status: string; active_mappings: Record<string, string> }> {
    const response = await apiClient.post(`/datasets/${datasetId}/mappings`, {
      mappings,
    });
    return response.data;
  },

  /** Sends natural-language query to the AI Analyst Agent */
  async sendMessage(
    datasetId: string,
    message: string,
    confirmedMappings?: Record<string, string>
  ): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(`/datasets/${datasetId}/chat`, {
      message,
      confirmed_mappings: confirmedMappings,
    });
    return response.data;
  },

  /** Deletes an in-memory dataset session */
  async deleteSession(datasetId: string): Promise<{ status: string }> {
    const response = await apiClient.delete(`/datasets/${datasetId}`);
    return response.data;
  },

  /** Health check endpoint */
  async checkHealth(): Promise<{ status: string; llm_configured: boolean; model: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

/**
 * Unit tests for the API client functions.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { getCV, updateCV, uploadCV, getPreviewUrl, healthCheck } from './api';
import { mockCVData } from './test/test-utils';

// Mock axios
vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return {
    default: {
      create: vi.fn(() => mockInstance),
      ...mockInstance,
    },
  };
});

// Get the mocked instance
const api = axios.create() as unknown as {
  get: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('getCV', () => {
  it('returns CV data on success', async () => {
    api.get.mockResolvedValueOnce({ data: mockCVData });
    const result = await getCV();
    expect(result).toEqual(mockCVData);
  });

  it('returns null when no CV exists', async () => {
    api.get.mockResolvedValueOnce({ data: null });
    const result = await getCV();
    expect(result).toBeNull();
  });

  it('calls the correct endpoint', async () => {
    api.get.mockResolvedValueOnce({ data: null });
    await getCV();
    expect(api.get).toHaveBeenCalledWith('/api/cv');
  });
});

describe('updateCV', () => {
  it('sends CV data and returns result', async () => {
    api.put.mockResolvedValueOnce({ data: mockCVData });
    const result = await updateCV(mockCVData);
    expect(result).toEqual(mockCVData);
  });

  it('calls PUT /api/cv', async () => {
    api.put.mockResolvedValueOnce({ data: mockCVData });
    await updateCV(mockCVData);
    expect(api.put).toHaveBeenCalledWith('/api/cv', mockCVData);
  });
});

describe('uploadCV', () => {
  it('sends file as FormData', async () => {
    api.post.mockResolvedValueOnce({ data: mockCVData });
    const file = new File(['content'], 'resume.pdf', { type: 'application/pdf' });
    const result = await uploadCV(file);
    expect(result).toEqual(mockCVData);
    expect(api.post).toHaveBeenCalled();
    const callArgs = api.post.mock.calls[0];
    expect(callArgs[0]).toBe('/api/cv/upload');
    expect(callArgs[1]).toBeInstanceOf(FormData);
  });
});

describe('getPreviewUrl', () => {
  it('returns the preview URL', () => {
    expect(getPreviewUrl()).toBe('/api/cv/preview');
  });
});

describe('healthCheck', () => {
  it('returns health status', async () => {
    api.get.mockResolvedValueOnce({ data: { status: 'ok' } });
    const result = await healthCheck();
    expect(result).toEqual({ status: 'ok' });
  });

  it('calls GET /api/health', async () => {
    api.get.mockResolvedValueOnce({ data: { status: 'ok' } });
    await healthCheck();
    expect(api.get).toHaveBeenCalledWith('/api/health');
  });
});

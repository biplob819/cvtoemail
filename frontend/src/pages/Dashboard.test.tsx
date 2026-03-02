/**
 * Tests for the Dashboard page component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/test-utils';
import Dashboard from './Dashboard';
import * as api from '../api';
import { mockCVData } from '../test/test-utils';

// Mock the entire API module
vi.mock('../api', () => ({
  getCV: vi.fn(),
  getDashboardStats: vi.fn(),
  getRecentJobs: vi.fn(),
  getSystemStatus: vi.fn(),
}));

const mockGetCV = api.getCV as ReturnType<typeof vi.fn>;
const mockGetDashboardStats = api.getDashboardStats as ReturnType<typeof vi.fn>;
const mockGetRecentJobs = api.getRecentJobs as ReturnType<typeof vi.fn>;
const mockGetSystemStatus = api.getSystemStatus as ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();
  // Default dashboard data mocks so the regular dashboard renders
  mockGetDashboardStats.mockResolvedValue({
    active_sources: 0,
    new_jobs_24h: 0,
    cvs_sent_7d: 0,
    last_scan: null,
    total_jobs: 0,
    total_applications: 0,
  });
  mockGetRecentJobs.mockResolvedValue([]);
  mockGetSystemStatus.mockResolvedValue({ celery_running: true, next_scan: null });
});

describe('Dashboard', () => {
  describe('Loading state', () => {
    it('shows skeleton loaders initially', () => {
      mockGetCV.mockReturnValue(new Promise(() => {})); // never resolves
      render(<Dashboard />);
      const skeletons = screen.getAllByRole('status');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('First-launch onboarding (no CV)', () => {
    it('shows welcome message when no CV exists', async () => {
      mockGetCV.mockResolvedValueOnce(null);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText(/welcome to auto job apply/i)).toBeInTheDocument();
      });
    });

    it('shows Upload CV button', async () => {
      mockGetCV.mockResolvedValueOnce(null);
      render(<Dashboard />);
      await waitFor(() => {
        // Button text "Upload Your CV" + setup step "Upload your CV" -- use getAllByText
        const matches = screen.getAllByText(/upload your cv/i);
        expect(matches.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('shows Add Job Source button', async () => {
      mockGetCV.mockResolvedValueOnce(null);
      render(<Dashboard />);
      await waitFor(() => {
        // Button text "Add Job Source" + setup step "Add job sources" -- use getAllByText
        const matches = screen.getAllByText(/add job source/i);
        expect(matches.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('shows setup steps', async () => {
      mockGetCV.mockResolvedValueOnce(null);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Setup Steps')).toBeInTheDocument();
        expect(screen.getByText('Upload your CV')).toBeInTheDocument();
        expect(screen.getByText('Add job sources')).toBeInTheDocument();
        expect(screen.getByText('Configure settings')).toBeInTheDocument();
      });
    });
  });

  describe('Regular dashboard (CV exists)', () => {
    it('shows Dashboard heading', async () => {
      mockGetCV.mockResolvedValueOnce(mockCVData);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });
    });

    it('shows stats cards', async () => {
      mockGetCV.mockResolvedValueOnce(mockCVData);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Active Sources')).toBeInTheDocument();
        expect(screen.getByText('New Jobs (24h)')).toBeInTheDocument();
        expect(screen.getByText('CVs Sent (7d)')).toBeInTheDocument();
        expect(screen.getByText('Last Scan')).toBeInTheDocument();
      });
    });

    it('shows Recent Jobs section', async () => {
      mockGetCV.mockResolvedValueOnce(mockCVData);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText('Recent Jobs')).toBeInTheDocument();
      });
    });

    it('shows empty jobs message', async () => {
      mockGetCV.mockResolvedValueOnce(mockCVData);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText(/no jobs discovered/i)).toBeInTheDocument();
      });
    });

    it('shows system status', async () => {
      mockGetCV.mockResolvedValueOnce(mockCVData);
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText(/celery worker/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error handling', () => {
    it('shows onboarding when API fails', async () => {
      mockGetCV.mockRejectedValueOnce(new Error('Network error'));
      render(<Dashboard />);
      await waitFor(() => {
        expect(screen.getByText(/welcome to auto job apply/i)).toBeInTheDocument();
      });
    });
  });
});

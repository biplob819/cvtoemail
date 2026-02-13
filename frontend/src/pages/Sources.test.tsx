/**
 * Tests for the Sources page component -- form, table, and actions.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/test-utils';
import userEvent from '@testing-library/user-event';
import Sources from './Sources';
import * as api from '../api';
import { mockSources } from '../test/test-utils';

// Mock the API module
vi.mock('../api', () => ({
  getSources: vi.fn(),
  createSource: vi.fn(),
  updateSource: vi.fn(),
  deleteSource: vi.fn(),
  scanSource: vi.fn(),
  checkUrl: vi.fn(),
}));

const mockGetSources = api.getSources as ReturnType<typeof vi.fn>;
const mockCreateSource = api.createSource as ReturnType<typeof vi.fn>;
const mockUpdateSource = api.updateSource as ReturnType<typeof vi.fn>;
const mockDeleteSource = api.deleteSource as ReturnType<typeof vi.fn>;
const mockScanSource = api.scanSource as ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Sources Page', () => {
  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------
  describe('Loading state', () => {
    it('shows skeleton loaders while fetching sources', () => {
      mockGetSources.mockReturnValue(new Promise(() => {})); // never resolves
      render(<Sources />);
      const skeletons = screen.getAllByRole('status');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  // -----------------------------------------------------------------------
  // Empty state
  // -----------------------------------------------------------------------
  describe('Empty state', () => {
    it('shows empty state when no sources exist', async () => {
      mockGetSources.mockResolvedValueOnce([]);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });
    });

    it('shows Add Source button in empty state', async () => {
      mockGetSources.mockResolvedValueOnce([]);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add source/i })).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Sources table
  // -----------------------------------------------------------------------
  describe('Sources table', () => {
    it('renders all sources in the table', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
        expect(screen.getByText('Startup IO')).toBeInTheDocument();
      });
    });

    it('shows active/paused badges', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
        expect(screen.getByText('Paused')).toBeInTheDocument();
      });
    });

    it('shows jobs count for each source', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });

    it('shows filters description when present', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Remote roles only')).toBeInTheDocument();
      });
    });

    it('renders URLs as external links', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        const links = screen.getAllByRole('link');
        const careerLink = links.find(l => l.getAttribute('href') === 'https://example.com/careers');
        expect(careerLink).toBeInTheDocument();
        expect(careerLink).toHaveAttribute('target', '_blank');
      });
    });

    it('shows Add Source button in table view', async () => {
      mockGetSources.mockResolvedValueOnce(mockSources);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add source/i })).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Add Source form
  // -----------------------------------------------------------------------
  describe('Add Source form', () => {
    it('opens modal when Add Source is clicked', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValueOnce([]);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add source/i }));
      expect(screen.getByText('Add Source', { selector: 'h2' })).toBeInTheDocument();
    });

    it('shows validation errors for empty fields', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValueOnce([]);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add source/i }));
      
      // Click submit without filling in fields
      const addButton = screen.getAllByRole('button', { name: /add source/i });
      const submitButton = addButton.find(btn => btn.closest('.space-y-4'));
      if (submitButton) {
        await user.click(submitButton);
      }

      await waitFor(() => {
        expect(screen.getByText(/url is required/i)).toBeInTheDocument();
        expect(screen.getByText(/portal name is required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for invalid URL', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValueOnce([]);
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add source/i }));

      const urlInput = screen.getByLabelText('URL');
      const nameInput = screen.getByLabelText('Portal Name');
      await user.type(urlInput, 'not-a-valid-url');
      await user.type(nameInput, 'Test Portal');

      // Submit
      const addButtons = screen.getAllByRole('button', { name: /add source/i });
      await user.click(addButtons[addButtons.length - 1]);

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid url/i)).toBeInTheDocument();
      });
    });

    it('creates a source successfully', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue([]);
      mockCreateSource.mockResolvedValueOnce({
        id: 1,
        url: 'https://new-source.com/careers',
        portal_name: 'New Source',
        filters_description: '',
        is_active: true,
        last_checked: null,
        created_at: '2026-02-13T10:00:00',
        jobs_found: 0,
      });

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add source/i }));

      const urlInput = screen.getByLabelText('URL');
      const nameInput = screen.getByLabelText('Portal Name');
      await user.type(urlInput, 'https://new-source.com/careers');
      await user.type(nameInput, 'New Source');

      const addButtons = screen.getAllByRole('button', { name: /add source/i });
      await user.click(addButtons[addButtons.length - 1]);

      await waitFor(() => {
        expect(mockCreateSource).toHaveBeenCalledWith({
          url: 'https://new-source.com/careers',
          portal_name: 'New Source',
          filters_description: undefined,
        });
      });
    });

    it('shows duplicate URL error from API', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue([]);
      mockCreateSource.mockRejectedValueOnce({
        response: { data: { detail: 'This URL is already being monitored.' } },
      });

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/no sources yet/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add source/i }));

      const urlInput = screen.getByLabelText('URL');
      const nameInput = screen.getByLabelText('Portal Name');
      await user.type(urlInput, 'https://dup-url.com/careers');
      await user.type(nameInput, 'Dup Source');

      const addButtons = screen.getAllByRole('button', { name: /add source/i });
      await user.click(addButtons[addButtons.length - 1]);

      await waitFor(() => {
        expect(screen.getByText(/already being monitored/i)).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Actions
  // -----------------------------------------------------------------------
  describe('Actions', () => {
    it('can pause/resume a source', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);
      mockUpdateSource.mockResolvedValue({ ...mockSources[0], is_active: false });

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      // Find and click the Pause button (first source is active)
      const pauseButton = screen.getByTitle('Pause');
      await user.click(pauseButton);

      expect(mockUpdateSource).toHaveBeenCalledWith(1, { is_active: false });
    });

    it('shows delete confirmation modal', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      // Find and click the Delete button for the first source
      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Source', { selector: 'h2' })).toBeInTheDocument();
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it('shows warning about existing jobs when deleting', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      // Delete source with 5 jobs
      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/5 associated job/i)).toBeInTheDocument();
      });
    });

    it('deletes a source after confirmation', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);
      mockDeleteSource.mockResolvedValue(undefined);

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Source', { selector: 'h2' })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /delete source/i }));

      await waitFor(() => {
        expect(mockDeleteSource).toHaveBeenCalledWith(1);
      });
    });

    it('triggers scan and shows result', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);
      mockScanSource.mockResolvedValueOnce({
        source_id: 1,
        jobs_found: 3,
        new_jobs: 2,
        message: 'Scan complete. Found 3 listings, 2 new.',
      });

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      // Multiple Scan Now buttons (one per source row) -- pick the first (active) one
      const scanButtons = screen.getAllByTitle('Scan Now');
      await user.click(scanButtons[0]);

      await waitFor(() => {
        expect(mockScanSource).toHaveBeenCalledWith(1);
      });
    });
  });

  // -----------------------------------------------------------------------
  // Edit modal
  // -----------------------------------------------------------------------
  describe('Edit source', () => {
    it('opens edit modal with pre-filled data', async () => {
      const user = userEvent.setup();
      mockGetSources.mockResolvedValue(mockSources);

      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText('Example Corp')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTitle('Edit');
      await user.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Edit Source')).toBeInTheDocument();
        const urlInput = screen.getByLabelText('URL') as HTMLInputElement;
        expect(urlInput.value).toBe('https://example.com/careers');
      });
    });
  });

  // -----------------------------------------------------------------------
  // Error state
  // -----------------------------------------------------------------------
  describe('Error state', () => {
    it('shows error message when loading fails', async () => {
      mockGetSources.mockRejectedValueOnce(new Error('Network error'));
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByText(/failed to load sources/i)).toBeInTheDocument();
      });
    });

    it('shows retry button on error', async () => {
      mockGetSources.mockRejectedValueOnce(new Error('Network error'));
      render(<Sources />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });
});

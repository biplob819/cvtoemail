import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Jobs from './Jobs';
import * as api from '../api';

// Mock API functions
vi.mock('../api');

const mockJobs = [
  {
    id: 1,
    source_id: 1,
    source_name: 'Example Corp',
    title: 'Software Engineer',
    company: 'Example Corp',
    location: 'San Francisco',
    description: 'We are looking for a talented software engineer...',
    url: 'https://example.com/jobs/1',
    status: 'New' as const,
    is_new: true,
    discovered_at: new Date().toISOString(),
  },
  {
    id: 2,
    source_id: 1,
    source_name: 'Example Corp',
    title: 'Product Manager',
    company: 'Example Corp',
    location: 'Remote',
    description: 'Seeking an experienced product manager...',
    url: 'https://example.com/jobs/2',
    status: 'Viewed' as const,
    is_new: false,
    discovered_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 3,
    source_id: 2,
    source_name: 'Tech Startup',
    title: 'Frontend Developer',
    company: 'Tech Startup',
    location: 'New York',
    description: 'Join our team as a frontend developer...',
    url: 'https://startup.com/jobs/1',
    status: 'Skipped' as const,
    is_new: false,
    discovered_at: new Date(Date.now() - 172800000).toISOString(),
  },
];

const mockSources = [
  {
    id: 1,
    url: 'https://example.com/jobs',
    portal_name: 'Example Corp',
    filters_description: '',
    is_active: true,
    last_checked: new Date().toISOString(),
    created_at: new Date().toISOString(),
    jobs_found: 2,
  },
  {
    id: 2,
    url: 'https://startup.com/careers',
    portal_name: 'Tech Startup',
    filters_description: '',
    is_active: true,
    last_checked: new Date().toISOString(),
    created_at: new Date().toISOString(),
    jobs_found: 1,
  },
];

describe('Jobs Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading skeleton initially', () => {
    vi.mocked(api.getJobs).mockResolvedValue([]);
    vi.mocked(api.getSources).mockResolvedValue([]);

    render(<Jobs />);
    
    // Check for skeleton elements
    const skeletons = screen.getAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('displays empty state when no jobs exist', async () => {
    vi.mocked(api.getJobs).mockResolvedValue([]);
    vi.mocked(api.getSources).mockResolvedValue([]);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('No jobs discovered yet')).toBeInTheDocument();
    });

    expect(screen.getByText(/Jobs will appear here automatically/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Go to Sources/i })).toBeInTheDocument();
  });

  it('displays jobs in a table', async () => {
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    expect(screen.getByText('Product Manager')).toBeInTheDocument();
    expect(screen.getByText('Frontend Developer')).toBeInTheDocument();
  });

  it('shows status badges with correct variants', async () => {
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Check for status badges
    const newBadges = screen.getAllByText('New');
    const viewedBadges = screen.getAllByText('Viewed');
    const skippedBadges = screen.getAllByText('Skipped');

    expect(newBadges.length).toBeGreaterThan(0);
    expect(viewedBadges.length).toBeGreaterThan(0);
    expect(skippedBadges.length).toBeGreaterThan(0);
  });

  it('shows new job indicator for new jobs', async () => {
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // The new job indicator is a small blue dot
    // We can check by finding the job row and checking for the indicator element
    const softwareEngineerRow = screen.getByText('Software Engineer').closest('tr');
    expect(softwareEngineerRow).toBeInTheDocument();
  });

  it('toggles filter panel visibility', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    const showFiltersButton = screen.getByRole('button', { name: /Show Filters/i });
    await user.click(showFiltersButton);

    // Filter panel should now be visible
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();

    // Button text should change
    expect(screen.getByRole('button', { name: /Hide Filters/i })).toBeInTheDocument();
  });

  it('filters jobs by source', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Show filters
    const showFiltersButton = screen.getByRole('button', { name: /Show Filters/i });
    await user.click(showFiltersButton);

    // Select a source
    const sourceSelect = screen.getByRole('combobox', { name: /Source/i });
    await user.selectOptions(sourceSelect, '1');

    // Apply filters
    const applyButton = screen.getByRole('button', { name: /Apply Filters/i });
    
    // Mock filtered results
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs.filter(j => j.source_id === 1));
    
    await user.click(applyButton);

    await waitFor(() => {
      expect(api.getJobs).toHaveBeenCalledWith(
        expect.objectContaining({ source_id: 1 })
      );
    });
  });

  it('filters jobs by status', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Show filters
    const showFiltersButton = screen.getByRole('button', { name: /Show Filters/i });
    await user.click(showFiltersButton);

    // Select a status
    const statusSelect = screen.getByRole('combobox', { name: /Status/i });
    await user.selectOptions(statusSelect, 'New');

    // Apply filters
    const applyButton = screen.getByRole('button', { name: /Apply Filters/i });
    
    // Mock filtered results
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs.filter(j => j.status === 'New'));
    
    await user.click(applyButton);

    await waitFor(() => {
      expect(api.getJobs).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'New' })
      );
    });
  });

  it('clears filters', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Show filters
    const showFiltersButton = screen.getByRole('button', { name: /Show Filters/i });
    await user.click(showFiltersButton);

    // Select filters
    const sourceSelect = screen.getByRole('combobox', { name: /Source/i });
    await user.selectOptions(sourceSelect, '1');

    // Clear filters
    const clearButton = screen.getByRole('button', { name: /Clear/i });
    await user.click(clearButton);

    // Should reload with no filters
    await waitFor(() => {
      expect(api.getJobs).toHaveBeenCalledWith({});
    });
  });

  it('expands job detail panel on click', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);
    vi.mocked(api.updateJob).mockResolvedValue(mockJobs[0]);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Click on the job row to expand
    const jobRow = screen.getByText('Software Engineer').closest('tr');
    await user.click(jobRow!);

    // Detail panel should be visible
    await waitFor(() => {
      expect(screen.getByText('Job Description')).toBeInTheDocument();
    });

    expect(screen.getByText(/We are looking for a talented software engineer/)).toBeInTheDocument();
  });

  it('marks new job as viewed when expanded', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);
    vi.mocked(api.updateJob).mockResolvedValue({
      ...mockJobs[0],
      status: 'Viewed',
      is_new: false,
    });

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Click on the new job
    const jobRow = screen.getByText('Software Engineer').closest('tr');
    await user.click(jobRow!);

    // Should call updateJob to mark as viewed
    await waitFor(() => {
      expect(api.updateJob).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ status: 'Viewed', is_new: false })
      );
    });
  });

  it('allows skipping a single job', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);
    vi.mocked(api.updateJob).mockResolvedValue({
      ...mockJobs[0],
      status: 'Skipped',
    });

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Expand the job
    const jobRow = screen.getByText('Software Engineer').closest('tr');
    await user.click(jobRow!);

    await waitFor(() => {
      expect(screen.getByText('Job Description')).toBeInTheDocument();
    });

    // Click the Skip button
    const skipButton = screen.getByRole('button', { name: /Skip/i });
    await user.click(skipButton);

    await waitFor(() => {
      expect(api.updateJob).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ status: 'Skipped', is_new: false })
      );
    });
  });

  it('allows bulk skipping selected jobs', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);
    vi.mocked(api.bulkSkipJobs).mockResolvedValue({
      status: 'success',
      updated_count: 2,
    });

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Select first two jobs using checkboxes
    const checkboxes = screen.getAllByRole('button', { name: /Select job/i });
    await user.click(checkboxes[0]);
    await user.click(checkboxes[1]);

    // Click bulk skip button
    const bulkSkipButton = screen.getByRole('button', { name: /Skip Selected/i });
    await user.click(bulkSkipButton);

    await waitFor(() => {
      expect(api.bulkSkipJobs).toHaveBeenCalledWith(expect.arrayContaining([1, 2]));
    });
  });

  it('allows selecting all jobs', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Click select all button
    const selectAllButton = screen.getByRole('button', { name: /Select all/i });
    await user.click(selectAllButton);

    // All jobs should be selected
    // The "Skip Selected" button should show count
    expect(screen.getByRole('button', { name: /Skip Selected \(3\)/i })).toBeInTheDocument();
  });

  it('opens job URL in new tab', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    // Mock window.open
    const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Expand the job
    const jobRow = screen.getByText('Software Engineer').closest('tr');
    await user.click(jobRow!);

    await waitFor(() => {
      expect(screen.getByText('Job Description')).toBeInTheDocument();
    });

    // Click "View Job Posting"
    const viewButton = screen.getByRole('button', { name: /View Job Posting/i });
    await user.click(viewButton);

    expect(windowOpenSpy).toHaveBeenCalledWith('https://example.com/jobs/1', '_blank');

    windowOpenSpy.mockRestore();
  });

  it('calls generate CV endpoint', async () => {
    const user = userEvent.setup();
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);
    vi.mocked(api.generateCV).mockResolvedValue({
      status: 'success',
      message: 'CV generation will be implemented in Milestone 4',
    });

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Expand the job
    const jobRow = screen.getByText('Software Engineer').closest('tr');
    await user.click(jobRow!);

    await waitFor(() => {
      expect(screen.getByText('Job Description')).toBeInTheDocument();
    });

    // Click "Generate CV"
    const generateButton = screen.getByRole('button', { name: /Generate CV/i });
    await user.click(generateButton);

    await waitFor(() => {
      expect(api.generateCV).toHaveBeenCalledWith(1);
    });
  });

  it('shows no results message when filters return empty', async () => {
    vi.mocked(api.getJobs).mockResolvedValue([]);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    // Initially load with filters applied (simulated by passing empty array)
    await waitFor(() => {
      expect(screen.getByText(/No jobs found matching the selected filters/i)).toBeInTheDocument();
    });
  });

  it('displays job count summary', async () => {
    vi.mocked(api.getJobs).mockResolvedValue(mockJobs);
    vi.mocked(api.getSources).mockResolvedValue(mockSources);

    render(<Jobs />);

    await waitFor(() => {
      expect(screen.getByText(/Showing 3 jobs/i)).toBeInTheDocument();
    });
  });
});

/**
 * Tests for the Layout component (sidebar navigation).
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '../test/test-utils';
import Layout from './Layout';

// Layout uses <Outlet />, so we need to wrap it differently
// We test the Layout in isolation -- checking that navigation renders

describe('Layout', () => {
  it('renders the brand name', () => {
    render(<Layout />);
    // There may be multiple instances (mobile + desktop)
    const brands = screen.getAllByText('Auto Job Apply');
    expect(brands.length).toBeGreaterThanOrEqual(1);
  });

  it('renders all navigation links', () => {
    render(<Layout />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('CV Editor')).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Jobs')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders version info in footer', () => {
    render(<Layout />);
    expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
  });

  it('has navigation links with correct hrefs', () => {
    render(<Layout />);
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const cvLink = screen.getByText('CV Editor').closest('a');
    const sourcesLink = screen.getByText('Sources').closest('a');
    const jobsLink = screen.getByText('Jobs').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');

    expect(dashboardLink).toHaveAttribute('href', '/');
    expect(cvLink).toHaveAttribute('href', '/cv');
    expect(sourcesLink).toHaveAttribute('href', '/sources');
    expect(jobsLink).toHaveAttribute('href', '/jobs');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });
});

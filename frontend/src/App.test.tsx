/**
 * Tests for the App component (routing setup).
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

// Mock all pages to avoid complex dependencies
vi.mock('./pages/Dashboard', () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}));
vi.mock('./pages/CVEditor', () => ({
  default: () => <div data-testid="cv-page">CV Editor Page</div>,
}));
vi.mock('./pages/Sources', () => ({
  default: () => <div data-testid="sources-page">Sources Page</div>,
}));
vi.mock('./pages/Jobs', () => ({
  default: () => <div data-testid="jobs-page">Jobs Page</div>,
}));
vi.mock('./pages/Settings', () => ({
  default: () => <div data-testid="settings-page">Settings Page</div>,
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(document.body).toBeTruthy();
  });

  it('renders the layout with sidebar', () => {
    render(<App />);
    // Layout should show "Auto Job Apply" brand
    const brands = screen.getAllByText('Auto Job Apply');
    expect(brands.length).toBeGreaterThanOrEqual(1);
  });

  it('renders Dashboard page on root route', async () => {
    // Set URL to root
    window.history.pushState({}, '', '/');
    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  it('shows all navigation items', () => {
    render(<App />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('CV Editor')).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Jobs')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});

/**
 * Shared test utilities -- custom render with Router wrapper, mock data.
 */
import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import type { ReactElement } from 'react';
import type { CVData, JobSource } from '../types';

/**
 * Custom render that wraps components in BrowserRouter.
 */
function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...options,
  });
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };

/**
 * Sample CV data for testing.
 */
export const mockCVData: CVData = {
  id: 1,
  personal_info: {
    name: 'Jane Doe',
    email: 'jane@example.com',
    phone: '+1-555-0100',
    location: 'San Francisco, CA',
    linkedin: 'https://linkedin.com/in/janedoe',
    website: 'https://janedoe.dev',
  },
  summary: 'Experienced software engineer with 6+ years building scalable web applications.',
  work_experience: [
    {
      title: 'Senior Software Engineer',
      company: 'TechCorp',
      duration: 'Jan 2021 - Present',
      achievements: [
        'Led a team of 5 engineers',
        'Reduced API latency by 40%',
      ],
    },
  ],
  education: [
    {
      degree: 'B.S. Computer Science',
      institution: 'UC Berkeley',
      year: '2018',
      details: 'Cum Laude',
    },
  ],
  skills: ['Python', 'FastAPI', 'React', 'TypeScript'],
  certifications: [
    { name: 'AWS Solutions Architect', issuer: 'AWS', year: '2023' },
  ],
  raw_text: 'Raw CV text here',
  updated_at: '2026-02-13T10:00:00',
};

/**
 * Empty CV data for testing onboarding states.
 */
export const emptyCVData: CVData = {
  personal_info: {
    name: '',
    email: '',
    phone: '',
    location: '',
  },
  summary: '',
  work_experience: [],
  education: [],
  skills: [],
  certifications: [],
};

/**
 * Sample job sources for testing.
 */
export const mockSources: JobSource[] = [
  {
    id: 1,
    url: 'https://example.com/careers',
    portal_name: 'Example Corp',
    filters_description: 'Remote roles only',
    is_active: true,
    last_checked: '2026-02-13T10:00:00',
    created_at: '2026-02-01T09:00:00',
    jobs_found: 5,
  },
  {
    id: 2,
    url: 'https://startup.io/jobs',
    portal_name: 'Startup IO',
    filters_description: '',
    is_active: false,
    last_checked: null,
    created_at: '2026-02-05T12:00:00',
    jobs_found: 0,
  },
];

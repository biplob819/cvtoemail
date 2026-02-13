/**
 * Unit tests for shared UI components (Button, Input, Card, Badge, Modal, Skeleton, Table).
 */
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '../test/test-utils';
import { Button, Input, Card, Badge, Modal, Skeleton, Table, TableHeader, TableRow, TableCell } from './ui';

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('applies primary variant by default', () => {
    render(<Button>Primary</Button>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('bg-primary');
  });

  it('applies secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('border-border');
  });

  it('applies danger variant', () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('bg-danger');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is disabled when loading', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows spinner when loading', () => {
    render(<Button loading>Loading</Button>);
    // Should not show children text when loading
    expect(screen.queryByText('Loading')).not.toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Click</Button>);
    await user.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

describe('Input', () => {
  it('renders without label', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="Name" />);
    expect(screen.getByText('Name')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText('Invalid email')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('sets aria-invalid when error exists', () => {
    render(<Input error="Required" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('accepts user input', async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Type here" />);
    const input = screen.getByPlaceholderText('Type here');
    await user.type(input, 'Hello World');
    expect(input).toHaveValue('Hello World');
  });
});

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

describe('Card', () => {
  it('renders children', () => {
    render(<Card><p>Card content</p></Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('applies default variant', () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText('Default').className).toContain('bg-surface');
  });

  it('applies success variant', () => {
    render(<Badge variant="success">Done</Badge>);
    expect(screen.getByText('Done').className).toContain('text-success');
  });

  it('applies warning variant', () => {
    render(<Badge variant="warning">Pending</Badge>);
    expect(screen.getByText('Pending').className).toContain('text-warning');
  });

  it('applies danger variant', () => {
    render(<Badge variant="danger">Error</Badge>);
    expect(screen.getByText('Error').className).toContain('text-danger');
  });

  it('applies info variant', () => {
    render(<Badge variant="info">Info</Badge>);
    expect(screen.getByText('Info').className).toContain('text-primary');
  });
});

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

describe('Modal', () => {
  it('does not render when closed', () => {
    render(<Modal open={false} onClose={() => {}}>Content</Modal>);
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('renders when open', () => {
    render(<Modal open={true} onClose={() => {}}>Modal Content</Modal>);
    expect(screen.getByText('Modal Content')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<Modal open={true} onClose={() => {}} title="My Modal">Body</Modal>);
    expect(screen.getByText('My Modal')).toBeInTheDocument();
  });

  it('has dialog role', () => {
    render(<Modal open={true} onClose={() => {}}>Content</Modal>);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Modal open={true} onClose={onClose} title="Test">Body</Modal>);
    await user.click(screen.getByLabelText('Close modal'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose on Escape key', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Modal open={true} onClose={onClose}>Body</Modal>);
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

describe('Skeleton', () => {
  it('renders with role status', () => {
    render(<Skeleton />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders with custom dimensions', () => {
    render(<Skeleton width={200} height={40} />);
    const el = screen.getByRole('status');
    expect(el.style.width).toBe('200px');
    expect(el.style.height).toBe('40px');
  });

  it('renders with string dimensions', () => {
    render(<Skeleton width="100%" height="2rem" />);
    const el = screen.getByRole('status');
    expect(el.style.width).toBe('100%');
    expect(el.style.height).toBe('2rem');
  });

  it('has loading aria-label', () => {
    render(<Skeleton />);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Table
// ---------------------------------------------------------------------------

describe('Table', () => {
  it('renders table structure', () => {
    render(
      <Table>
        <TableHeader>
          <TableCell header>Name</TableCell>
          <TableCell header>Email</TableCell>
        </TableHeader>
        <tbody>
          <TableRow>
            <TableCell>John</TableCell>
            <TableCell>john@test.com</TableCell>
          </TableRow>
        </tbody>
      </Table>
    );

    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('john@test.com')).toBeInTheDocument();
  });

  it('renders header cells as <th>', () => {
    render(
      <Table>
        <TableHeader>
          <TableCell header>Header</TableCell>
        </TableHeader>
        <tbody>
          <TableRow>
            <TableCell>Data</TableCell>
          </TableRow>
        </tbody>
      </Table>
    );

    expect(screen.getByText('Header').tagName).toBe('TH');
    expect(screen.getByText('Data').tagName).toBe('TD');
  });
});

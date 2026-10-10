import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Badge, Button, Chip, Segmented, Switch, Select } from '../components/primitives';

describe('UI Primitives', () => {
  it('renders Badge with variants and children', () => {
    render(<Badge variant="critical">Critical Issue</Badge>);
    expect(screen.getByText('Critical Issue')).toBeTruthy();
  });

  it('renders Button and responds to clicks', () => {
    const handleClick = vi.fn();
    render(
      <Button variant="primary" onClick={handleClick}>
        Analyze
      </Button>
    );
    const btn = screen.getByRole('button', { name: 'Analyze' });
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('renders disabled Button without click handler execution', () => {
    const handleClick = vi.fn();
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    );
    const btn = screen.getByRole('button', { name: 'Disabled' });
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('renders Chip with remove button', () => {
    const handleRemove = vi.fn();
    render(
      <Chip active onRemove={handleRemove}>
        Filter: High
      </Chip>
    );
    expect(screen.getByText('Filter: High')).toBeTruthy();
    const removeBtn = screen.getByRole('button', { name: 'Remove' });
    fireEvent.click(removeBtn);
    expect(handleRemove).toHaveBeenCalledOnce();
  });

  it('renders Segmented options and selects an option', () => {
    const handleChange = vi.fn();
    render(
      <Segmented
        options={[
          { value: 'all', label: 'All' },
          { value: 'active', label: 'Active' },
        ]}
        value="all"
        onChange={handleChange}
      />
    );
    const activeOption = screen.getByRole('radio', { name: 'Active' });
    fireEvent.click(activeOption);
    expect(handleChange).toHaveBeenCalledWith('active');
  });

  it('renders Switch and toggles state', () => {
    const handleChange = vi.fn();
    render(<Switch checked={false} onChange={handleChange} label="Enable ML" />);
    const switchControl = screen.getByRole('switch', { name: 'Enable ML' });
    fireEvent.click(switchControl);
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it('renders Select and handles change', () => {
    const handleChange = vi.fn();
    render(
      <Select
        aria-label="Select mode"
        options={[
          { value: 'python', label: 'Python' },
          { value: 'javascript', label: 'JavaScript' },
        ]}
        value="python"
        onChange={handleChange}
      />
    );
    const selectControl = screen.getByLabelText('Select mode');
    fireEvent.change(selectControl, { target: { value: 'javascript' } });
    expect(handleChange).toHaveBeenCalledWith('javascript');
  });
});

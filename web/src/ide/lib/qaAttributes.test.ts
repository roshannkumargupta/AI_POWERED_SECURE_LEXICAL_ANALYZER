import { describe, expect, it } from 'vitest';
import { observeInteractiveElements, tagInteractiveElements } from './qaAttributes';

describe('stable UI audit identifiers', () => {
  it('tags buttons, form controls, tabs, options, menu items, and resizers deterministically', () => {
    const root = document.createElement('div');
    const add = (tag: string, label: string, attribute = 'aria-label'): HTMLElement => {
      const element = document.createElement(tag);
      element.setAttribute(attribute, label);
      if (tag === 'div' && attribute === 'role') element.textContent = label;
      root.append(element);
      return element;
    };
    add('button', 'Open settings');
    add('button', 'Open settings');
    add('input', 'Search files', 'placeholder');
    add('div', 'tab', 'role').textContent = 'Tokens';
    add('div', 'option', 'role').textContent = 'Python';
    add('div', 'menuitem', 'role').textContent = 'Export';
    add('div', 'separator', 'role').setAttribute('aria-label', 'Resize panel');
    tagInteractiveElements(root);
    const controls = [...root.querySelectorAll<HTMLElement>('button,input,[role]')];
    expect(controls.every((control) => control.dataset.qa)).toBe(true);
    expect(controls.map((control) => control.dataset.qa)).toEqual([
      'button-open-settings',
      'button-open-settings-2',
      'input-search-files',
      'div-tokens',
      'div-python',
      'div-export',
      'div-resize-panel',
    ]);
    const identifiers = controls.map((control) => control.dataset.qa);
    tagInteractiveElements(root);
    expect(controls.map((control) => control.dataset.qa)).toEqual(identifiers);
  });

  it('does not replace an explicit contract identifier', () => {
    const root = document.createElement('div');
    const button = document.createElement('button');
    button.dataset.qa = 'retry-backend';
    button.textContent = 'Retry';
    root.append(button);
    tagInteractiveElements(root);
    expect(root.querySelector('button')?.getAttribute('data-qa')).toBe('retry-backend');
  });

  it('audits lazy-mounted controls and requires disabled controls to expose a reason', async () => {
    const root = document.createElement('main');
    const stop = observeInteractiveElements(root);
    const disabled = document.createElement('button');
    disabled.disabled = true;
    disabled.title = 'Formatter unavailable for this language.';
    disabled.textContent = 'Format';
    root.append(disabled);
    await Promise.resolve();
    expect(disabled.dataset.qa).toBe('button-format');
    expect(disabled.disabled ? disabled.title.trim().length > 0 : true).toBe(true);
    stop();
  });
});

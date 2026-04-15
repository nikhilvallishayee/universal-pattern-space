// Transparency mode state shared across components
import { writable } from 'svelte/store';

/**
 * When true, every query response auto-expands its reasoning trace inline.
 * Toggled from QueryInterface advanced options or the TransparencyPanel header.
 */
export const transparencyMode = writable(false);

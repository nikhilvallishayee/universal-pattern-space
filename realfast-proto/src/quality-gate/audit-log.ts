/**
 * Audit Trail System
 *
 * SOC2 compliance requires full auditability:
 * - Every AI decision logged
 * - Every human intervention tracked
 * - Immutable history with timestamps
 * - Exportable for compliance review
 */

import { AuditEntry } from './types.js';

export interface AuditLogOptions {
  maxEntries?: number; // default: unlimited
  retention?: number; // milliseconds to keep entries, default: unlimited
}

export class AuditLog {
  private entries: AuditEntry[] = [];
  private options: Required<AuditLogOptions>;

  constructor(options?: AuditLogOptions) {
    this.options = {
      maxEntries: options?.maxEntries || Infinity,
      retention: options?.retention || Infinity,
    };
  }

  /**
   * Append an audit entry
   */
  log(entry: Omit<AuditEntry, 'timestamp'>): void {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: Date.now(),
    };

    // Add entry
    this.entries.push(fullEntry);

    // Enforce max entries limit
    if (this.entries.length > this.options.maxEntries) {
      this.entries.shift(); // remove oldest
    }

    // Clean up expired entries based on retention policy
    if (this.options.retention !== Infinity) {
      const cutoff = Date.now() - this.options.retention;
      this.entries = this.entries.filter(e => e.timestamp >= cutoff);
    }
  }

  /**
   * Log an agent action
   */
  logAgentAction(agentId: string, action: string, details: string, metadata?: Record<string, unknown>): void {
    this.log({
      action,
      actor: 'agent',
      actorId: agentId,
      details,
      metadata,
    });
  }

  /**
   * Log a quality gate action
   */
  logQualityGateAction(action: string, details: string, metadata?: Record<string, unknown>): void {
    this.log({
      action,
      actor: 'quality-gate',
      details,
      metadata,
    });
  }

  /**
   * Log a human action
   */
  logHumanAction(humanId: string, action: string, details: string, metadata?: Record<string, unknown>): void {
    this.log({
      action,
      actor: 'human',
      actorId: humanId,
      details,
      metadata,
    });
  }

  /**
   * Get full audit log
   */
  getLog(): ReadonlyArray<AuditEntry> {
    return [...this.entries];
  }

  /**
   * Get log entries for a specific actor
   */
  getLogByActor(actor: 'agent' | 'quality-gate' | 'human', actorId?: string): AuditEntry[] {
    return this.entries.filter(
      e => e.actor === actor && (actorId === undefined || e.actorId === actorId)
    );
  }

  /**
   * Get log entries for a specific action
   */
  getLogByAction(action: string): AuditEntry[] {
    return this.entries.filter(e => e.action === action);
  }

  /**
   * Get log entries within a time range
   */
  getLogByTimeRange(startTime: number, endTime: number): AuditEntry[] {
    return this.entries.filter(e => e.timestamp >= startTime && e.timestamp <= endTime);
  }

  /**
   * Search log entries by details content
   */
  searchLog(query: string): AuditEntry[] {
    const lowerQuery = query.toLowerCase();
    return this.entries.filter(e => e.details.toLowerCase().includes(lowerQuery));
  }

  /**
   * Export log as JSON
   */
  exportJSON(): string {
    return JSON.stringify(
      {
        exported: new Date().toISOString(),
        totalEntries: this.entries.length,
        entries: this.entries.map(e => ({
          ...e,
          timestamp: new Date(e.timestamp).toISOString(),
        })),
      },
      null,
      2
    );
  }

  /**
   * Export log as CSV
   */
  exportCSV(): string {
    const headers = ['Timestamp', 'Actor', 'ActorID', 'Action', 'Details', 'Metadata'];
    const rows = this.entries.map(e => [
      new Date(e.timestamp).toISOString(),
      e.actor,
      e.actorId || '',
      e.action,
      e.details.replace(/"/g, '""'), // escape quotes
      e.metadata ? JSON.stringify(e.metadata).replace(/"/g, '""') : '',
    ]);

    return [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
  }

  /**
   * Export log as human-readable text
   */
  exportText(): string {
    return this.entries
      .map(e => {
        const timestamp = new Date(e.timestamp).toISOString();
        const actorInfo = e.actorId ? `${e.actor}(${e.actorId})` : e.actor;
        return `[${timestamp}] ${actorInfo}: ${e.action}\n  ${e.details}${
          e.metadata ? `\n  Metadata: ${JSON.stringify(e.metadata)}` : ''
        }`;
      })
      .join('\n\n');
  }

  /**
   * Export log in specified format
   */
  exportLog(format: 'json' | 'csv' | 'text'): string {
    switch (format) {
      case 'json':
        return this.exportJSON();
      case 'csv':
        return this.exportCSV();
      case 'text':
        return this.exportText();
      default:
        throw new Error(`Unknown export format: ${format}`);
    }
  }

  /**
   * Clear all entries (use with caution!)
   */
  clear(): void {
    this.entries = [];
  }

  /**
   * Get audit statistics
   */
  getStats(): {
    totalEntries: number;
    entriesByActor: Record<string, number>;
    entriesByAction: Record<string, number>;
    oldestEntry?: Date;
    newestEntry?: Date;
  } {
    const entriesByActor: Record<string, number> = {};
    const entriesByAction: Record<string, number> = {};

    for (const entry of this.entries) {
      entriesByActor[entry.actor] = (entriesByActor[entry.actor] || 0) + 1;
      entriesByAction[entry.action] = (entriesByAction[entry.action] || 0) + 1;
    }

    return {
      totalEntries: this.entries.length,
      entriesByActor,
      entriesByAction,
      oldestEntry: this.entries.length > 0 ? new Date(this.entries[0].timestamp) : undefined,
      newestEntry:
        this.entries.length > 0 ? new Date(this.entries[this.entries.length - 1].timestamp) : undefined,
    };
  }

  /**
   * Merge another audit log into this one
   */
  merge(otherLog: AuditLog): void {
    const otherEntries = otherLog.getLog();
    this.entries.push(...otherEntries);
    this.entries.sort((a, b) => a.timestamp - b.timestamp);

    // Enforce limits after merge
    if (this.entries.length > this.options.maxEntries) {
      this.entries = this.entries.slice(-this.options.maxEntries);
    }
  }

  /**
   * Create a snapshot of current log state
   */
  snapshot(): AuditLog {
    const snapshot = new AuditLog(this.options);
    snapshot.entries = [...this.entries];
    return snapshot;
  }
}

/**
 * Factory function for easy instantiation
 */
export function createAuditLog(options?: AuditLogOptions): AuditLog {
  return new AuditLog(options);
}

/**
 * Global audit log (singleton pattern)
 */
let globalAuditLog: AuditLog | null = null;

export function getGlobalAuditLog(): AuditLog {
  if (!globalAuditLog) {
    globalAuditLog = new AuditLog();
  }
  return globalAuditLog;
}

export function setGlobalAuditLog(log: AuditLog): void {
  globalAuditLog = log;
}

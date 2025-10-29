import { notificationService } from './notificationService';

export interface BackendReadinessStatus {
  initialization_complete: boolean;
  services_ready: Record<string, boolean>;
  ready_for_requests: boolean;
  estimated_ready_time?: string;
  pending_services?: string[];
  timestamp: string;
  error?: string;
}

export interface ReadinessState {
  isReady: boolean;
  isChecking: boolean;
  status?: BackendReadinessStatus;
  lastCheck?: Date;
  retryCount: number;
  maxRetries: number;
}

class BackendReadinessService {
  private state: ReadinessState = {
    isReady: false,
    isChecking: false,
    retryCount: 0,
    maxRetries: 15 // 15 attempts = ~45 seconds max wait (reduced)
  };

  private listeners: Set<() => void> = new Set();
  private checkInterval: NodeJS.Timeout | undefined = undefined;
  private readonly CHECK_INTERVAL = 2000; // 2 seconds (faster)
  private readonly INITIAL_DELAY = 1000; // 1 second initial delay (faster)

  constructor() {
    // Start checking readiness immediately
    this.startReadinessCheck();
  }

  // State management
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener());
  }

  getState(): ReadinessState {
    return { ...this.state };
  }

  // Main readiness checking logic
  private async startReadinessCheck(): Promise<void> {
    if (this.state.isChecking) return;

    console.log('🔄 Starting backend readiness check...');
    notificationService.info('Connecting to backend...', { duration: 3000 });

    this.state.isChecking = true;
    this.state.retryCount = 0;
    this.notify();

    // Initial delay to let backend start
    await new Promise(resolve => setTimeout(resolve, this.INITIAL_DELAY));

    // Start periodic checking
    this.checkInterval = setInterval(() => {
      this.checkBackendReadiness();
    }, this.CHECK_INTERVAL);

    // Do first check immediately
    await this.checkBackendReadiness();
  }

  private async checkBackendReadiness(): Promise<void> {
    if (this.state.retryCount >= this.state.maxRetries) {
      this.handleMaxRetriesReached();
      return;
    }

    try {
      this.state.retryCount++;
      this.state.lastCheck = new Date();

      console.log(`🔍 Backend readiness check attempt ${this.state.retryCount}/${this.state.maxRetries}`);

      const response = await fetch('/api/health/ready', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(3000) // Reduced from 5 to 3 seconds
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const status: BackendReadinessStatus = await response.json();
      this.state.status = status;

      if (status.ready_for_requests && status.initialization_complete) {
        this.handleBackendReady();
      } else {
        this.handleBackendNotReady(status);
      }

    } catch (error: any) {
      this.handleCheckError(error);
    }

    this.notify();
  }

  private handleBackendReady(): void {
    console.log('✅ Backend is ready!');
    
    this.state.isReady = true;
    this.state.isChecking = false;
    
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = undefined;
    }

    notificationService.success('Backend connected successfully!', { duration: 2000 });
    this.notify();
  }

  private handleBackendNotReady(status: BackendReadinessStatus): void {
    const pendingServices = status.pending_services || [];
    const estimatedTime = status.estimated_ready_time || 'unknown';
    
    console.log(`⏳ Backend initializing... Pending: ${pendingServices.join(', ')} (ETA: ${estimatedTime})`);
    
    // Show progress notification
    if (this.state.retryCount % 3 === 0) { // Every 9 seconds
      const message = pendingServices.length > 0 
        ? `Initializing services: ${pendingServices.slice(0, 2).join(', ')}${pendingServices.length > 2 ? '...' : ''}`
        : 'Backend services starting up...';
      
      notificationService.info(message, { duration: 3000 });
    }
  }

  private handleCheckError(error: any): void {
    const isConnectionError = error.name === 'TypeError' || 
                             error.message?.includes('fetch') || 
                             error.message?.includes('ECONNREFUSED') ||
                             error.message?.includes('Failed to fetch');

    if (isConnectionError) {
      console.log(`🔄 Backend not yet available (attempt ${this.state.retryCount}/${this.state.maxRetries})`);
      
      // Show connection status every few attempts
      if (this.state.retryCount % 4 === 0) { // Every 12 seconds
        notificationService.info('Waiting for backend to start...', { duration: 3000 });
      }
    } else {
      console.error(`❌ Backend readiness check failed:`, error);
      
      if (this.state.retryCount % 5 === 0) { // Every 15 seconds
        notificationService.warning(`Backend connection issue: ${error.message}`, { duration: 4000 });
      }
    }
  }

  private handleMaxRetriesReached(): void {
    console.error('❌ Max retries reached. Backend may not be available.');
    
    this.state.isChecking = false;
    
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = undefined;
    }

    notificationService.error(
      'Backend connection failed. Please refresh the page or contact support.',
      { duration: 10000 }
    );
    
    this.notify();
  }

  // Public methods
  async waitForBackend(timeoutMs: number = 120000): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.state.isReady) {
        resolve(true);
        return;
      }

      const timeout = setTimeout(() => {
        unsubscribe();
        resolve(false);
      }, timeoutMs);

      const unsubscribe = this.subscribe(() => {
        if (this.state.isReady) {
          clearTimeout(timeout);
          unsubscribe();
          resolve(true);
        } else if (!this.state.isChecking && this.state.retryCount >= this.state.maxRetries) {
          clearTimeout(timeout);
          unsubscribe();
          resolve(false);
        }
      });
    });
  }

  async forceRecheck(): Promise<void> {
    if (this.state.isChecking) return;

    console.log('🔄 Force rechecking backend readiness...');
    this.state.retryCount = 0;
    await this.startReadinessCheck();
  }

  isBackendReady(): boolean {
    return this.state.isReady;
  }

  getReadinessStatus(): BackendReadinessStatus | undefined {
    return this.state.status;
  }

  // Cleanup
  destroy(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = undefined;
    }
    this.listeners.clear();
  }
}

export const backendReadinessService = new BackendReadinessService();
export default backendReadinessService;
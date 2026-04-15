/**
 * Mobile-specific utilities and enhancements for GödelOS
 */

export class MobileEnhancer {
  constructor() {
    this.isMobile = this.detectMobile();
    this.isTouch = this.detectTouch();
    this.orientation = this.getOrientation();
    this.sidebarElement = null;
    this.setupMobileOptimizations();
  }

  detectMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
      || window.innerWidth <= 768;
  }

  detectTouch() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }

  getOrientation() {
    return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
  }

  setupMobileOptimizations() {
    if (!this.isMobile) return;

    // Add mobile class to body for CSS targeting
    document.body.classList.add('mobile-device');
    
    // Set initial mobile device properties
    document.body.classList.toggle('portrait', this.orientation === 'portrait');
    document.body.classList.toggle('landscape', this.orientation === 'landscape');

    // Prevent zoom on input focus (iOS)
    this.preventIOSZoom();

    // Setup touch feedback
    this.setupTouchFeedback();

    // Handle orientation changes
    this.handleOrientationChange();

    // Optimize scrolling performance
    this.optimizeScrolling();

    // Setup viewport height fix for mobile browsers
    this.setupViewportHeightFix();
    
    // Initialize sidebar for mobile
    this.initializeMobileSidebar();
  }

  preventIOSZoom() {
    // Prevent zoom on input focus for iOS devices
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport && /iPhone|iPad|iPod/i.test(navigator.userAgent)) {
      let originalContent = viewport.getAttribute('content');
      
      document.addEventListener('focusin', () => {
        viewport.setAttribute('content', originalContent + ', user-scalable=0');
      });
      
      document.addEventListener('focusout', () => {
        viewport.setAttribute('content', originalContent);
      });
    }
  }

  setupTouchFeedback() {
    // Add visual feedback for touch interactions
    document.addEventListener('touchstart', (e) => {
      const target = e.target.closest('button, .nav-item, .expand-btn, [role="button"]');
      if (target) {
        target.classList.add('touch-active');
      }
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      setTimeout(() => {
        document.querySelectorAll('.touch-active').forEach(el => {
          el.classList.remove('touch-active');
        });
      }, 150);
    }, { passive: true });
  }

  handleOrientationChange() {
    window.addEventListener('orientationchange', () => {
      // Force layout recalculation after orientation change
      setTimeout(() => {
        this.orientation = this.getOrientation();
        document.body.classList.toggle('landscape', this.orientation === 'landscape');
        document.body.classList.toggle('portrait', this.orientation === 'portrait');
        
        // Trigger a custom event for components to respond to orientation changes
        window.dispatchEvent(new CustomEvent('mobileOrientationChange', {
          detail: { orientation: this.orientation }
        }));
      }, 100);
    });
  }

  optimizeScrolling() {
    // Add momentum scrolling to scrollable elements
    const scrollableElements = document.querySelectorAll('.main-content, .nav-sections, .component-container');
    scrollableElements.forEach(el => {
      el.style.webkitOverflowScrolling = 'touch';
      el.style.overflowScrolling = 'touch';
    });
  }

  setupViewportHeightFix() {
    // Fix for mobile viewport height issues (address bar)
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', () => {
      setTimeout(setVH, 100);
    });
  }

  // Initialize mobile sidebar behavior
  initializeMobileSidebar() {
    // Wait for DOM to be ready
    const initSidebar = () => {
      this.sidebarElement = document.querySelector('.sidebar');
      if (this.sidebarElement && this.isMobile) {
        // Ensure sidebar starts collapsed on mobile
        this.sidebarElement.classList.add('collapsed');
        
        // Add mobile overlay click handler
        this.setupSidebarOverlayClose();
      }
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initSidebar);
    } else {
      initSidebar();
    }
  }

  // Setup click outside to close sidebar on mobile
  setupSidebarOverlayClose() {
    if (!this.sidebarElement) return;

    document.addEventListener('click', (e) => {
      if (this.isMobile && !this.sidebarElement.classList.contains('collapsed')) {
        // Check if click is outside sidebar and not on toggle button
        const isClickInsideSidebar = this.sidebarElement.contains(e.target);
        const isToggleButton = e.target.closest('.sidebar-toggle');
        
        if (!isClickInsideSidebar && !isToggleButton) {
          this.sidebarElement.classList.add('collapsed');
        }
      }
    });

    // Close sidebar on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isMobile && !this.sidebarElement.classList.contains('collapsed')) {
        this.sidebarElement.classList.add('collapsed');
      }
    });
  }

  // Gesture recognition utilities
  setupSwipeGestures(element, callbacks = {}) {
    if (!this.isTouch) return;

    let startX, startY, startTime;
    const threshold = 50; // Minimum distance for swipe
    const timeThreshold = 300; // Maximum time for swipe

    element.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      startX = touch.clientX;
      startY = touch.clientY;
      startTime = Date.now();
    }, { passive: true });

    element.addEventListener('touchend', (e) => {
      if (!startX || !startY) return;

      const touch = e.changedTouches[0];
      const endX = touch.clientX;
      const endY = touch.clientY;
      const endTime = Date.now();

      const deltaX = endX - startX;
      const deltaY = endY - startY;
      const deltaTime = endTime - startTime;

      if (deltaTime > timeThreshold) return;

      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      if (absX > threshold && absX > absY) {
        // Horizontal swipe
        if (deltaX > 0 && callbacks.swipeRight) {
          callbacks.swipeRight(e);
        } else if (deltaX < 0 && callbacks.swipeLeft) {
          callbacks.swipeLeft(e);
        }
      } else if (absY > threshold && absY > absX) {
        // Vertical swipe
        if (deltaY > 0 && callbacks.swipeDown) {
          callbacks.swipeDown(e);
        } else if (deltaY < 0 && callbacks.swipeUp) {
          callbacks.swipeUp(e);
        }
      }

      // Reset
      startX = startY = null;
    }, { passive: true });
  }

  // Haptic feedback (if supported)
  vibrate(pattern = [100]) {
    if ('vibrate' in navigator && this.isMobile) {
      navigator.vibrate(pattern);
    }
  }

  // Check if app is running in standalone mode (PWA)
  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  // Network status monitoring for mobile
  setupNetworkMonitoring() {
    if ('connection' in navigator) {
      const connection = navigator.connection;
      
      const updateConnectionStatus = () => {
        document.body.classList.toggle('slow-connection', 
          connection.effectiveType === '2g' || connection.effectiveType === 'slow-2g');
      };

      updateConnectionStatus();
      connection.addEventListener('change', updateConnectionStatus);
    }

    // Online/offline status
    window.addEventListener('online', () => {
      document.body.classList.remove('offline');
      window.dispatchEvent(new CustomEvent('connectionRestored'));
    });

    window.addEventListener('offline', () => {
      document.body.classList.add('offline');
      window.dispatchEvent(new CustomEvent('connectionLost'));
    });
  }
}

// Touch-friendly interaction helpers
export function makeTouchFriendly(element) {
  if (!element) return;

  // Ensure minimum touch target size
  const rect = element.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    element.style.minWidth = '44px';
    element.style.minHeight = '44px';
    element.style.display = 'flex';
    element.style.alignItems = 'center';
    element.style.justifyContent = 'center';
  }

  // Add touch-friendly class
  element.classList.add('touch-friendly');
}

// Initialize mobile enhancements
export function initializeMobileEnhancements() {
  const enhancer = new MobileEnhancer();
  
  // Setup swipe gestures for sidebar
  const setupSidebarSwipes = () => {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebar && mainContent && enhancer.isMobile) {
      // Swipe right from left edge to open sidebar
      enhancer.setupSwipeGestures(document.body, {
        swipeRight: (e) => {
          // Only open if swipe starts from left edge
          const startX = e.changedTouches[0]?.clientX || 0;
          if (startX < 50 && sidebar.classList.contains('collapsed')) {
            sidebar.classList.remove('collapsed');
            enhancer.vibrate([50]);
          }
        },
        swipeLeft: (e) => {
          // Close sidebar if it's open
          if (!sidebar.classList.contains('collapsed')) {
            sidebar.classList.add('collapsed');
            enhancer.vibrate([50]);
          }
        }
      });
      
      console.log('📱 Mobile swipe gestures setup for sidebar');
    }
  };

  // Setup swipe gestures when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupSidebarSwipes);
  } else {
    setTimeout(setupSidebarSwipes, 100); // Small delay to ensure elements exist
  }

  // Setup network monitoring
  enhancer.setupNetworkMonitoring();

  // Make interactive elements touch-friendly
  const makeTouchFriendlyElements = () => {
    const interactiveElements = document.querySelectorAll('button, .nav-item, .expand-btn, [role="button"]');
    interactiveElements.forEach(makeTouchFriendly);
  };

  // Apply touch-friendly improvements when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', makeTouchFriendlyElements);
  } else {
    makeTouchFriendlyElements();
  }

  // Re-apply on dynamic content changes
  const observer = new MutationObserver(() => {
    makeTouchFriendlyElements();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  return enhancer;
}
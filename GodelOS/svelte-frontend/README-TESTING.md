# GödelOS Frontend Testing Guide

This document provides comprehensive information about the Playwright testing infrastructure for the GödelOS enhanced cognitive frontend.

## Overview

The testing suite validates the enhanced cognitive features, API connectivity, user interactions, and overall system integration of the GödelOS frontend application. Tests are designed to ensure the enhanced metacognition and autonomous knowledge acquisition features work correctly.

## Test Structure

### Test Files

1. **enhanced-cognitive-features.spec.js** - Core enhanced cognitive feature testing
2. **api-connectivity.spec.js** - Backend API integration and connectivity
3. **user-interactions.spec.js** - User interface interactions and visual elements
4. **enhanced-cognitive-components.spec.js** - Specific enhanced cognitive component testing
5. **system-integration.spec.js** - End-to-end system functionality

### Key Features Tested

#### Enhanced Cognitive Features
- ✅ Enhanced Cognitive Dashboard
- ✅ Stream of Consciousness Monitor
- ✅ Autonomous Learning Monitor
- ✅ Real-time cognitive event streaming
- ✅ Enhanced metacognition visualization
- ✅ NEW badge and featured item indicators

#### API Integration
- ✅ Enhanced cognitive API endpoints
- ✅ WebSocket connectivity
- ✅ Real-time data synchronization
- ✅ Error handling and recovery
- ✅ Health monitoring

#### User Experience
- ✅ Navigation functionality
- ✅ Visual enhancements (sparkle, shimmer effects)
- ✅ Responsive design
- ✅ Accessibility features
- ✅ Performance optimization

## Running Tests

### Prerequisites

1. Ensure the GödelOS backend is running:
   ```bash
   ./start-godelos.sh
   ```

2. Ensure the frontend development server is running:
   ```bash
   cd svelte-frontend
   npm run dev
   ```

### Test Commands

#### Run All Tests
```bash
npm test
```

#### Run Tests with Browser UI
```bash
npm run test:headed
```

#### Interactive Test UI
```bash
npm run test:ui
```

#### Debug Mode
```bash
npm run test:debug
```

#### Specific Test Suites
```bash
# Enhanced cognitive features only
npm run test:enhanced

# API connectivity tests
npm run test:api

# System integration tests
npm run test:integration

# User interaction tests
npm run test:interactions
```

#### View Test Reports
```bash
npm run test:report
```

## Test Configuration

### Browser Support
- ✅ Chromium (Chrome/Edge)
- ✅ Firefox
- ✅ WebKit (Safari)

### Viewport Testing
- ✅ Desktop (1920x1080, 1366x768)
- ✅ Tablet (768x1024)
- ✅ Mobile (375x667)

### Performance Monitoring
- ✅ Navigation timing
- ✅ Memory usage tracking
- ✅ API response times
- ✅ Real-time data processing

## Test Data Requirements

### Expected UI Elements

The tests expect specific `data-testid` attributes on key elements:

#### Navigation Elements
- `app-container` - Main application container
- `sidebar-nav` - Navigation sidebar
- `sidebar-toggle` - Sidebar collapse/expand button
- `main-content` - Main content area

#### Navigation Sections
- `nav-section-core` - Core Features section
- `nav-section-enhanced` - Enhanced Cognition section
- `nav-section-analysis` - Analysis & Tools section
- `nav-section-system` - System Management section

#### Navigation Items
- `nav-item-dashboard` - Dashboard navigation
- `nav-item-enhanced` - Enhanced Dashboard navigation
- `nav-item-stream` - Stream of Consciousness navigation
- `nav-item-autonomous` - Autonomous Learning navigation
- `nav-item-cognitive` - Cognitive State navigation
- `nav-item-knowledge` - Knowledge Graph navigation
- `nav-item-query` - Query Interface navigation

#### Component Containers
- `enhanced-cognitive-dashboard` - Enhanced cognitive dashboard
- `stream-of-consciousness-monitor` - Stream monitor component
- `autonomous-learning-monitor` - Autonomous learning component
- `cognitive-state-monitor` - Cognitive state component
- `knowledge-graph` - Knowledge graph component
- `query-interface` - Query interface component

#### Status and Health
- `system-health` - System health indicator
- `connection-status` - WebSocket connection status
- `system-status` - Overall system status

### API Endpoints Tested

#### Enhanced Cognitive APIs
- `/api/enhanced-cognitive/health` - Health check
- `/api/enhanced-cognitive/status` - System status
- `/api/enhanced-cognitive/stream` - Cognitive stream data
- `/api/enhanced-cognitive/autonomous` - Autonomous learning data
- `/api/enhanced-cognitive/metrics` - Performance metrics

## Test Scenarios

### 1. Enhanced Cognitive Feature Validation

**Objective**: Verify enhanced cognitive features are accessible and functional

**Key Tests**:
- Navigation to enhanced cognitive sections
- NEW badge visibility on enhanced features
- Featured item indicators
- Component loading and rendering
- Real-time data updates

### 2. API Connectivity and Integration

**Objective**: Ensure robust backend communication

**Key Tests**:
- WebSocket connection establishment
- API endpoint availability
- Error handling and recovery
- Data synchronization
- Health monitoring

### 3. User Interaction Testing

**Objective**: Validate user interface responsiveness

**Key Tests**:
- Navigation interactions
- Hover effects and animations
- Modal dialogs
- Form submissions
- Keyboard navigation
- Accessibility compliance

### 4. Enhanced Cognitive Components

**Objective**: Test specific enhanced cognitive functionality

**Key Tests**:
- Enhanced Dashboard metrics display
- Stream of Consciousness real-time updates
- Autonomous Learning progress tracking
- Component state management
- Performance optimization

### 5. System Integration

**Objective**: End-to-end system functionality

**Key Tests**:
- Complete user workflows
- Cross-component data consistency
- Error resilience
- Performance under load
- Browser compatibility

## Expected Behaviors

### Enhanced Cognitive Features
- Enhanced Cognition section displays with NEW badge
- Featured items show visual enhancements (sparkle/shimmer)
- Real-time data streaming in Stream of Consciousness
- Autonomous learning metrics update automatically
- Enhanced dashboard shows comprehensive system overview

### Error Handling
- Graceful degradation when API endpoints are unavailable
- User-friendly error messages
- Automatic retry mechanisms
- Fallback states for missing data

### Performance
- Page load times under 5 seconds
- Navigation responses under 2 seconds
- Memory usage remains stable during extended use
- No critical console errors

## Troubleshooting

### Common Issues

#### Tests Failing Due to Timing
- Increase wait times in test configuration
- Check if backend services are fully initialized
- Verify WebSocket connections are established

#### Missing UI Elements
- Ensure `data-testid` attributes are present in components
- Check component rendering conditions
- Verify CSS classes for visual elements

#### API Connection Issues
- Confirm backend is running on correct port (8000)
- Check CORS configuration
- Verify enhanced cognitive router registration

#### Performance Issues
- Monitor memory usage during tests
- Check for memory leaks in long-running tests
- Optimize test execution order

### Debug Tips

1. **Use headed mode** to see browser interactions:
   ```bash
   npm run test:headed
   ```

2. **Enable debug mode** for step-by-step execution:
   ```bash
   npm run test:debug
   ```

3. **Check console output** for application errors

4. **Monitor network tab** for API call failures

5. **Use browser dev tools** during test execution

## Continuous Integration

### CI/CD Integration
Tests are designed to run in CI environments with:
- Headless browser execution
- Parallel test execution
- Comprehensive reporting
- Failure screenshots and videos

### Test Reports
- HTML reports with screenshots
- Performance metrics
- Coverage information
- Error details and stack traces

## Contributing

### Adding New Tests

1. Create test files in the `tests/` directory
2. Follow existing naming conventions
3. Use appropriate `data-testid` attributes
4. Include performance and accessibility checks
5. Add documentation for new test scenarios

### Test Best Practices

1. **Use reliable selectors** - Prefer `data-testid` over CSS selectors
2. **Wait for elements** - Use proper wait strategies
3. **Test user workflows** - Focus on real user scenarios
4. **Include error cases** - Test failure scenarios
5. **Monitor performance** - Track timing and memory usage

## Support

For issues with the testing infrastructure:
1. Check the troubleshooting section
2. Review test logs and reports
3. Verify system requirements
4. Contact the development team

---

*This testing guide ensures comprehensive validation of the GödelOS enhanced cognitive features and maintains high quality standards for the frontend application.*
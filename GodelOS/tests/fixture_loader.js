/**
 * Test fixture utilities for frontend tests
 */

export class FixtureLoader {
  static async loadFixture(fixtureName, subfolder = null) {
    const path = subfolder 
      ? `./fixtures/${subfolder}/${fixtureName}.json`
      : `./fixtures/${fixtureName}.json`;
    
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Fixture not found: ${path}`);
    }
    return response.json();
  }
  
  static async loadCognitiveState(stateName = 'default') {
    return this.loadFixture(stateName, 'cognitive_states');
  }
  
  static async loadApiResponse(endpoint) {
    return this.loadFixture(endpoint, 'api_responses');
  }
  
  static async loadSampleData(dataType) {
    return this.loadFixture(dataType, 'sample_data');
  }
}

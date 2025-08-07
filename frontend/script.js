document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Smart Traffic Predictor loaded successfully');
    
    const form = document.getElementById('predictForm');
    const resultsContainer = document.getElementById('results-container');
    const predictBtn = document.getElementById('predictBtn');
    
    // Initialize the dashboard
    initializeDashboard();
    
    function initializeDashboard() {
        console.log('🔧 Initializing dashboard...');
        
        // Set up form submission
        if (form) {
            form.addEventListener('submit', handlePrediction);
        }
        
        // Load initial data
        checkServerHealth();
        
        // Auto-load analytics when page loads
        setTimeout(() => {
            loadAnalytics();
        }, 1000);
    }
    
    // Navigation Functions
    window.showSection = function(sectionName) {
        console.log(`📍 Switching to section: ${sectionName}`);
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active class from all nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        const targetNav = document.getElementById(`nav-${sectionName}`);
        
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        if (targetNav) {
            targetNav.classList.add('active');
        }
        
        // Load data for specific sections
        switch(sectionName) {
            case 'analytics':
                loadAnalytics();
                break;
            case 'graphs':
                loadGraphs();
                break;
        }
    };
    
    // Prediction Handler
    async function handlePrediction(e) {
        e.preventDefault();
        console.log('🔄 Processing prediction request...');
        
        // Show loading state
        showPredictionLoading();
        
        try {
            // Get form data
            const formData = new FormData(form);
            const data = {
                day_of_week: formData.get('day_of_week') || 'Monday',
                season: formData.get('season') || 'Spring',
                location: formData.get('location') || 'East'
            };
            
            console.log('📤 Sending prediction data:', data);
            
            // Make API request
            const response = await fetch('https://roadtrafficbackend.onrender.com/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📥 Prediction result received:', result);
            
            if (result.success && result.prediction) {
                displayPredictionResults(result.prediction);
                showSuccessMessage('🎉 Traffic prediction completed successfully!');
            } else {
                throw new Error(result.error || 'No prediction data received');
            }
            
        } catch (error) {
            console.error('❌ Prediction error:', error);
            showErrorMessage(`⚠️ Prediction failed: ${error.message}`);
            hidePredictionResults();
        } finally {
            hidePredictionLoading();
        }
    }
    
    // Display Functions
    function displayPredictionResults(prediction) {
        console.log('🎯 Displaying prediction results:', prediction);
        
        const resultsTitle = document.getElementById('results-title');
        const hourlyPredictions = document.getElementById('hourly-predictions');
        
        if (!resultsTitle || !hourlyPredictions) {
            console.error('❌ Results elements not found');
            return;
        }
        
        // Update title
        resultsTitle.innerHTML = `🎯 Traffic Analysis: ${prediction.day_of_week}, ${prediction.season} - ${prediction.location} Zone`;
        
        // Display hourly predictions
        let hourlyHTML = '';
        
        prediction.hourly_predictions.forEach(hourData => {
            const isPeak = hourData.is_peak;
            const isHeavy = hourData.traffic_level === 'heavy';
            
            let cardClass = 'hour-card';
            if (isPeak) cardClass += ' peak';
            if (isHeavy) cardClass += ' heavy';
            
            let infoText = '';
            let statusIcon = '';
            
            if (isPeak && isHeavy) {
                infoText = '🚨 Critical Peak Hour';
                statusIcon = '🚨';
            } else if (isPeak) {
                infoText = '⚡ Peak Traffic Hour';
                statusIcon = '⚡';
            } else if (isHeavy) {
                infoText = '🚧 Heavy Traffic';
                statusIcon = '🚧';
            } else {
                infoText = '✅ Normal Flow';
                statusIcon = '✅';
            }
            
            hourlyHTML += `
                <div class="${cardClass}">
                    <div class="hour-time">${hourData.hour}:00</div>
                    <div class="traffic-level ${hourData.traffic_level}">
                        ${statusIcon} ${hourData.traffic_level.charAt(0).toUpperCase() + hourData.traffic_level.slice(1)}
                    </div>
                    <div class="hour-info">${infoText}</div>
                </div>
            `;
        });
        
        hourlyPredictions.innerHTML = hourlyHTML;
        
        // Show results with animation
        resultsContainer.style.display = 'block';
        setTimeout(() => {
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
    
    // Analytics Functions
    window.loadAnalytics = async function() {
        console.log('📊 Loading analytics dashboard...');
        
        const analyticsContent = document.getElementById('analytics-content');
        if (!analyticsContent) return;
        
        analyticsContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>Analyzing traffic patterns...</span>
            </div>
        `;
        
        try {
            const response = await fetch('https://roadtrafficbackend.onrender.com/analytics-dashboard');
            const data = await response.json();
            
            if (data.success) {
                displayAnalytics(data);
            } else {
                throw new Error(data.error || 'Failed to load analytics');
            }
        } catch (error) {
            console.error('❌ Analytics loading failed:', error);
            analyticsContent.innerHTML = `
                <div class="error-message" style="position: static; min-width: auto;">
                    ⚠️ Failed to load analytics: ${error.message}
                </div>
            `;
        }
    };
    
    function displayAnalytics(data) {
        const analyticsContent = document.getElementById('analytics-content');
        
        let analyticsHTML = '';
        
        // Server stats
        if (data.server_stats) {
            analyticsHTML += `
                <div class="analytics-grid">
                    <div class="stat-card">
                        <div class="stat-number">${data.server_stats.model_loaded ? '🟢' : '🔴'}</div>
                        <div class="stat-label">AI Model Status</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.server_stats.total_predictions || 0}</div>
                        <div class="stat-label">Total Predictions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">🚀</div>
                        <div class="stat-label">System Status</div>
                    </div>
                </div>
            `;
        }
        
        // Analytics data
        if (data.analytics && !data.analytics.message) {
            analyticsHTML += `
                <div class="analytics-grid">
                    <div class="stat-card">
                        <div class="stat-number">📅</div>
                        <div class="stat-label">Most Predicted: ${data.analytics.most_common_day || 'N/A'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">🌤️</div>
                        <div class="stat-label">Peak Season: ${data.analytics.most_common_season || 'N/A'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">📍</div>
                        <div class="stat-label">Hotspot: ${data.analytics.most_common_location || 'N/A'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.analytics.most_common_peak_hour || 'N/A'}</div>
                        <div class="stat-label">Peak Hour</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.analytics.most_common_heavy_hour || 'N/A'}</div>
                        <div class="stat-label">Heavy Traffic Hour</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${Math.round(data.analytics.average_peak_hours_per_day || 0)}</div>
                        <div class="stat-label">Avg Peak Hours/Day</div>
                    </div>
                </div>
            `;
        }
        
        analyticsContent.innerHTML = analyticsHTML || `
            <div style="text-align: center; padding: 50px;">
                <h3>📊 Analytics Intelligence Center</h3>
                <p style="color: #64748b; margin-top: 15px;">No analytics data available yet. Generate some predictions to unlock insights!</p>
                <div class="traffic-lights" style="margin-top: 30px;">
                    <div class="traffic-light red"></div>
                    <div class="traffic-light yellow"></div>
                    <div class="traffic-light green"></div>
                </div>
            </div>
        `;
    }
    
    // Graphs Functions
    window.loadGraphs = async function() {
        console.log('📈 Loading traffic graphs...');
        
        const graphsContent = document.getElementById('graphs-content');
        if (!graphsContent) return;
        
        graphsContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>Generating advanced visualizations...</span>
            </div>
        `;
        
        try {
            const response = await fetch('https://roadtrafficbackend.onrender.com/graphs');
            const data = await response.json();
            
            if (data.success && data.graph_data) {
                graphsContent.innerHTML = `
                    <div class="graph-container">
                        <h3>📊 Advanced Traffic Flow Visualizations</h3>
                        <p style="color: #64748b; margin-bottom: 25px; font-weight: 500;">
                            📅 Generated: ${new Date(data.timestamp).toLocaleString()} | 
                            🎯 Predictions Analyzed: ${data.prediction_count || 0}
                        </p>
                        <img src="data:image/png;base64,${data.graph_data}" class="graph-image" alt="Traffic Analysis Graphs">
                        <div class="info-panel">
                            <h4>📋 Comprehensive Analysis Includes:</h4>
                            <ul>
                                <li>📊 Hourly Traffic Distribution Patterns</li>
                                <li>⚡ Peak Hours Identification & Analysis</li>
                                <li>📍 Geographic Traffic Distribution</li>
                                <li>📅 Weekly Traffic Pattern Analysis</li>
                                <li>🌤️ Seasonal Traffic Variations</li>
                                <li>🚨 Heavy Traffic Hotspot Detection</li>
                            </ul>
                        </div>
                    </div>
                `;
            } else {
                throw new Error(data.error || 'No graph data received');
            }
        } catch (error) {
            console.error('❌ Graph loading failed:', error);
            graphsContent.innerHTML = `
                <div class="error-message" style="position: static; min-width: auto;">
                    ⚠️ Failed to load visualizations: ${error.message}
                </div>
                <div style="text-align: center; margin-top: 25px;">
                    <button class="nav-btn" onclick="loadGraphs()">🔄 Retry Loading</button>
                </div>
            `;
        }
    };
    
    // Utility Functions
    function showPredictionLoading() {
        predictBtn.innerHTML = `
            <div class="spinner" style="width: 20px; height: 20px; margin-right: 10px; border-width: 2px;"></div>
            🔄 Analyzing Traffic Patterns...
        `;
        predictBtn.disabled = true;
    }
    
    function hidePredictionLoading() {
        predictBtn.innerHTML = '🚀 Generate Traffic Prediction';
        predictBtn.disabled = false;
    }
    
    function hidePredictionResults() {
        resultsContainer.style.display = 'none';
    }
    
    function showSuccessMessage(message) {
        showMessage(message, 'success');
    }
    
    function showErrorMessage(message) {
        showMessage(message, 'error');
    }
    
    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.style.animation = 'slideInRight 0.4s ease-out reverse';
            setTimeout(() => {
                messageDiv.remove();
            }, 400);
        }, 3000);
    }
    
    async function checkServerHealth() {
        try {
            const response = await fetch('https://roadtrafficbackend.onrender.com/health');
            if (response.ok) {
                const health = await response.json();
                console.log('✅ Server health check passed:', health);
            }
        } catch (error) {
            console.log('❌ Server health check failed:', error);
            showErrorMessage('⚠️ Warning: Server connection issues detected');
        }
    }
});

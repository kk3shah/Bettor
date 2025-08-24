// 🎯 Bettor - Analysis Page JavaScript

class BettorAnalysis {
    constructor() {
        this.analysisData = null;
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Filter tabs
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.setFilter(filter);
            });
        });
    }

    async loadAnalysis(homeTeam, awayTeam) {
        console.log(`🔍 Loading analysis for ${homeTeam} vs ${awayTeam}`);
        
        try {
            // Show loading state
            this.showLoading();
            
            // Simulate loading steps
            this.simulateLoadingSteps();
            
            // Make API call
            const response = await fetch(`/api/analyze?home_team=${encodeURIComponent(homeTeam)}&away_team=${encodeURIComponent(awayTeam)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.analysisData = data;
            this.displayAnalysis(data);
            this.hideLoading();
            
        } catch (error) {
            console.error('❌ Analysis failed:', error);
            this.showError(error.message);
        }
    }

    simulateLoadingSteps() {
        const steps = document.querySelectorAll('.loading-step');
        
        setTimeout(() => {
            steps[0]?.classList.remove('active');
            steps[1]?.classList.add('active');
        }, 1000);
        
        setTimeout(() => {
            steps[1]?.classList.remove('active');
            steps[2]?.classList.add('active');
        }, 2000);
    }

    displayAnalysis(data) {
        console.log('📊 Displaying analysis results', data);
        console.log('📊 Data keys:', Object.keys(data));
        console.log('📊 All bets count:', data.all_bets ? data.all_bets.length : 'NO ALL_BETS');
        console.log('📊 Top bets count:', data.top_bets ? data.top_bets.length : 'NO TOP_BETS');
        
        // ✅ VALIDATION: Check if we have valid data
        if (!data || typeof data !== 'object') {
            console.error('❌ Invalid analysis data:', data);
            this.showError('Invalid analysis data received');
            return;
        }
        
        // Update match header (with fallback data)
        this.updateMatchHeader(data.match_info || {});
        
        // Update summary stats (with fallback data)
        this.updateSummaryStats(data.summary || {});
        
        // Display top bets
        this.displayTopBets(data.top_bets || []);
        
        // Display all bets (use top_bets as fallback if all_bets not present)
        this.displayAllBets(data.all_bets || data.top_bets || []);
        
        // No profit scenarios - using profitable odds thresholds instead
        
        // Animate values
        this.animateStats();
    }

    updateMatchHeader(matchInfo) {
        // ✅ NULL CHECK: Handle missing match info
        if (!matchInfo || typeof matchInfo !== 'object') {
            console.warn('⚠️ Missing match info, using defaults');
            matchInfo = {};
        }
        
        // Update analysis time safely
        try {
            const analysisTime = new Date(matchInfo.analysis_time || Date.now());
            const timeElement = document.getElementById('analysisTime');
            if (timeElement) {
                timeElement.textContent = analysisTime.toLocaleTimeString();
            }
        } catch (error) {
            console.warn('⚠️ Error updating analysis time:', error);
        }
        
        // Update lineup source
        const lineupSourceElement = document.getElementById('lineupSource');
        if (lineupSourceElement) {
            lineupSourceElement.textContent = matchInfo.lineup_source || 'Squad-based analysis';
        }
        
        // Update team logos
        const homeTeamLogo = document.getElementById('homeTeamLogo');
        const awayTeamLogo = document.getElementById('awayTeamLogo');
        
        if (homeTeamLogo && matchInfo.home_team_logo) {
            homeTeamLogo.src = matchInfo.home_team_logo;
            homeTeamLogo.style.display = 'inline-block';
        }
        
        if (awayTeamLogo && matchInfo.away_team_logo) {
            awayTeamLogo.src = matchInfo.away_team_logo;
            awayTeamLogo.style.display = 'inline-block';
        }
        
        // Update match time if available
        if (matchInfo.kickoff_time) {
            try {
                const kickoffTime = new Date(matchInfo.kickoff_time);
                const matchTimeElement = document.getElementById('matchTime');
                if (matchTimeElement) {
                    matchTimeElement.textContent = kickoffTime.toLocaleTimeString([], {
                        hour: '2-digit', 
                        minute: '2-digit'
                    });
                }
            } catch (error) {
                console.warn('⚠️ Error updating match time:', error);
            }
        }
    }

    updateSummaryStats(summary) {
        // ✅ NULL CHECK: Handle missing summary data
        if (!summary || typeof summary !== 'object') {
            console.warn('⚠️ Missing summary data, using defaults');
            summary = {};
        }
        
        // Update elements safely
        const totalOppsElement = document.getElementById('totalOpportunities');
        if (totalOppsElement) {
            totalOppsElement.textContent = summary.total_opportunities || 0;
        }
        
        const highConfElement = document.getElementById('highConfidenceBets');
        if (highConfElement) {
            highConfElement.textContent = summary.high_confidence_bets || 0;
        }
        
        const mediumConfElement = document.getElementById('mediumConfidenceBets');
        if (mediumConfElement) {
            mediumConfElement.textContent = summary.medium_confidence_bets || 0;
        }
    }

    displayTopBets(topBets) {
        const container = document.getElementById('topBetsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        // ✅ NULL CHECK: Handle undefined or empty topBets
        if (!topBets || !Array.isArray(topBets) || topBets.length === 0) {
            container.innerHTML = '<div class="no-bets">No betting opportunities available</div>';
            return;
        }
        
        topBets.slice(0, 6).forEach(bet => {
            const betElement = this.createBetCard(bet, false);
            container.appendChild(betElement);
        });
    }

    displayAllBets(allBets) {
        const container = document.getElementById('allBetsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        // ✅ NULL CHECK: Handle undefined or empty allBets (use top_bets as fallback)
        if (!allBets || !Array.isArray(allBets) || allBets.length === 0) {
            // Use top_bets as fallback for all_bets
            const fallbackBets = this.analysisData?.top_bets || [];
            if (fallbackBets.length === 0) {
                container.innerHTML = '<div class="no-bets">No detailed betting analysis available</div>';
                return;
            }
            allBets = fallbackBets;
        }
        
        allBets.forEach(bet => {
            const betElement = this.createBetCard(bet, true);
            container.appendChild(betElement);
        });
    }

    createBetCard(bet, detailed = false) {
        // ✅ NULL CHECK: Handle completely undefined bet object
        if (!bet || typeof bet !== 'object') {
            console.warn('⚠️ Invalid bet object:', bet);
            return document.createElement('div'); // Return empty div
        }
        
        const card = document.createElement('div');
        
        // Safe property access with fallbacks
        const confidence = bet.confidence || 'Medium';
        const modelProb = bet.model_probability_percent || 50;
        
        card.className = `bet-card ${confidence.toLowerCase()}-confidence`;
        card.dataset.confidence = confidence.toLowerCase();
        
        const probColor = modelProb > 40 ? 'var(--success-color)' : 
                         modelProb > 25 ? 'var(--warning-color)' : 'var(--text-muted)';
        
        // Handle both old and new data formats gracefully
        const playerName = bet.player || bet.player_name || 'Unknown Player';
        const shirtNumber = bet.shirt_number || bet.jersey_number || '';
        const position = bet.position || '';
        const team = bet.team || '';
        const market = bet.bet_description || bet.market || 'Unknown Market';
        const isTeamProp = bet.is_team_prop || false;
        const teamLogo = bet.team_logo || '';
        
        // Create player/team display with logo
        let playerDisplay = playerName;
        if (isTeamProp && teamLogo) {
            playerDisplay = `<img src="${teamLogo}" alt="${playerName}" class="team-logo-small"> ${playerName}`;
        }
        
        // New format fields (profitable odds thresholds)
        if (bet.min_profitable_odds_american && bet.min_profitable_odds_decimal) {
            card.innerHTML = `
                <div class="bet-header">
                    <div class="bet-player">
                        <div class="player-name">${playerDisplay}${!isTeamProp && shirtNumber ? ` (#${shirtNumber})` : ''}</div>
                        <div class="bet-market">${market}</div>
                        <div class="bet-position">${position}${team ? ` - ${team}` : ''}</div>
                    </div>
                    <div class="confidence-badge ${confidence.toLowerCase()}">${confidence}</div>
                </div>
                
                <div class="bet-details">
                    <div class="bet-detail">
                        <div class="detail-value" style="color: ${probColor}">${modelProb}%</div>
                        <div class="detail-label">Model Prob</div>
                    </div>
                    <div class="bet-detail">
                        <div class="detail-value">${bet.fair_odds_decimal || 'N/A'}</div>
                        <div class="detail-label">Fair Odds</div>
                    </div>
                    <div class="bet-detail">
                        <div class="detail-value" style="color: ${bet.final_score >= 70 ? 'var(--success-color)' : bet.final_score >= 60 ? 'var(--warning-color)' : 'var(--error-color)'}">${bet.final_score || 'N/A'}</div>
                        <div class="detail-label">Final Score</div>
                    </div>
                    <div class="bet-detail">
                        <div class="detail-value">${bet.apps_this_season || 'N/A'}</div>
                        <div class="detail-label">Apps</div>
                    </div>
                    <div class="bet-detail">
                        <div class="detail-value">${bet.avg_per_game || 'N/A'}</div>
                        <div class="detail-label">Avg/Game</div>
                    </div>
                </div>
                
                <div class="bet-threshold">
                    <div class="threshold-info">
                        <div class="threshold-label">💰 Profitable if odds ≥</div>
                        <div class="odds-input-container">
                            <input type="number" class="odds-input" value="${bet.min_profitable_odds_decimal}" step="0.01" min="1.01" onchange="updateProfit(this, ${bet.model_probability_percent})">
                            <div class="profit-display">
                                <span class="profit-value">+15%</span>
                                <span class="profit-label">Expected ROI</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Fallback for old format data
            card.innerHTML = `
                <div class="bet-header">
                    <div class="bet-player">
                        <div class="player-name">${playerName}</div>
                        <div class="bet-market">${bet.bet_description || bet.market}</div>
                    </div>
                    <div class="confidence-badge ${confidence.toLowerCase()}">${confidence}</div>
                </div>
                
                <div class="bet-details">
                    <div class="bet-detail">
                        <div class="detail-value" style="color: ${probColor}">${modelProb}%</div>
                        <div class="detail-label">Model Prob</div>
                    </div>
                    <div class="bet-detail">
                        <div class="detail-value">${bet.odds_american || bet.odds || 'N/A'}</div>
                        <div class="detail-label">Odds</div>
                    </div>
                </div>
                
                <div class="bet-note">
                    <small>⚠️ Old analysis format - refresh page for new profitable odds thresholds</small>
                </div>
            `;
        }
        
        return card;
    }

    displayScenarios(scenarios) {
        const container = document.getElementById('scenariosList');
        if (!container || !scenarios) return;
        
        container.innerHTML = '';
        
        scenarios.forEach(scenario => {
            const scenarioElement = this.createScenarioCard(scenario);
            container.appendChild(scenarioElement);
        });
    }

    createScenarioCard(scenario) {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        
        const profit = typeof scenario.profit === 'number' ? scenario.profit : 0;
        const roi = typeof scenario.roi === 'number' ? scenario.roi : 0;
        const isPositive = profit >= 0;
        
        card.innerHTML = `
            <div class="scenario-name">${scenario.name}</div>
            <div class="scenario-profit ${isPositive ? 'positive' : 'negative'}">
                ${BettorUtils.formatCurrency(Math.abs(profit))}
            </div>
            <div class="scenario-roi">${roi.toFixed(1)}% ROI</div>
        `;
        
        return card;
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update active tab
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.filter === filter);
        });
        
        // Filter bet cards
        this.filterBetCards();
    }

    filterBetCards() {
        const betCards = document.querySelectorAll('.bet-card');
        
        betCards.forEach(card => {
            const shouldShow = this.currentFilter === 'all' || 
                             card.dataset.confidence === this.currentFilter;
            card.style.display = shouldShow ? 'block' : 'none';
        });
    }

    animateStats() {
        // Animate summary values
        const stats = [
            { id: 'totalOpportunities', value: this.analysisData?.summary?.total_opportunities || 0 },
            { id: 'expectedROI', value: this.analysisData?.summary?.expected_roi_percent || 0, suffix: '%' },
            { id: 'totalStake', value: this.analysisData?.summary?.total_stake_recommended || 0, currency: true },
            { id: 'expectedProfit', value: this.analysisData?.summary?.expected_profit || 0, currency: true }
        ];
        
        stats.forEach(stat => {
            const element = document.getElementById(stat.id);
            if (element) {
                BettorUtils.animateValue(element, 0, stat.value, 1500);
            }
        });
    }

    showLoading() {
        document.getElementById('analysisLoading').style.display = 'flex';
        document.getElementById('analysisResults').style.display = 'none';
        document.getElementById('analysisError').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('analysisLoading').style.display = 'none';
        document.getElementById('analysisResults').style.display = 'block';
        document.getElementById('analysisError').style.display = 'none';
    }

    showError(message) {
        document.getElementById('analysisLoading').style.display = 'none';
        document.getElementById('analysisResults').style.display = 'none';
        document.getElementById('analysisError').style.display = 'flex';
        document.getElementById('errorMessage').textContent = message;
    }
}

// Global function to load analysis (called from HTML)
window.loadAnalysis = async (homeTeam, awayTeam) => {
    if (!window.bettorAnalysis) {
        window.bettorAnalysis = new BettorAnalysis();
    }
    await window.bettorAnalysis.loadAnalysis(homeTeam, awayTeam);
};

// Helper functions for formatting
window.BettorUtils = window.BettorUtils || {
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    formatPercentage: (value) => {
        return `${(value * 100).toFixed(1)}%`;
    },
    
    animateValue: (element, start, end, duration = 1000) => {
        const startTimestamp = performance.now();
        
        const step = (timestamp) => {
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = start + (end - start) * progress;
            
            if (element) {
                if (element.id.includes('Stake') || element.id.includes('Profit')) {
                    element.textContent = BettorUtils.formatCurrency(current);
                } else if (element.id.includes('ROI')) {
                    element.textContent = `${current.toFixed(1)}%`;
                } else {
                    element.textContent = Math.round(current);
                }
            }
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    }
};

// Dynamic profit calculation
function updateProfit(input, modelProbability) {
    const userOdds = parseFloat(input.value);
    const profitDisplay = input.parentElement.querySelector('.profit-value');
    const profitLabel = input.parentElement.querySelector('.profit-label');
    
    if (userOdds && userOdds > 1) {
        const stake = 10; // $10 stake
        const modelProbDecimal = modelProbability / 100; // Convert percentage to decimal
        
        // Calculate expected return on $10 stake
        const potentialWin = stake * (userOdds - 1); // Profit if bet wins
        const expectedReturn = (modelProbDecimal * potentialWin) - ((1 - modelProbDecimal) * stake);
        
        if (expectedReturn > 0) {
            profitDisplay.textContent = `+$${expectedReturn.toFixed(2)}`;
            profitDisplay.style.color = 'var(--success-color)';
            profitLabel.textContent = 'Expected Return ($10 stake)';
        } else {
            profitDisplay.textContent = `-$${Math.abs(expectedReturn).toFixed(2)}`;
            profitDisplay.style.color = 'var(--error-color)';
            profitLabel.textContent = 'Expected Loss ($10 stake)';
        }
        
        profitDisplay.style.display = 'block';
    } else {
        profitDisplay.style.display = 'none';
    }
}

console.log('📊 Analysis JavaScript loaded');

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
        console.log('📊 Displaying analysis results');
        
        // Update match header
        this.updateMatchHeader(data.match_info);
        
        // Update summary stats
        this.updateSummaryStats(data.summary);
        
        // Display top bets
        this.displayTopBets(data.top_bets);
        
        // Display all bets
        this.displayAllBets(data.all_bets);
        
        // Display profit scenarios
        this.displayScenarios(data.profit_scenarios);
        
        // Animate values
        this.animateStats();
    }

    updateMatchHeader(matchInfo) {
        // Update analysis time
        const analysisTime = new Date(matchInfo.analysis_time);
        document.getElementById('analysisTime').textContent = analysisTime.toLocaleTimeString();
        
        // Update lineup source
        document.getElementById('lineupSource').textContent = matchInfo.lineup_source || 'Squad-based analysis';
        
        // Update match time if available
        if (matchInfo.kickoff_time) {
            const kickoffTime = new Date(matchInfo.kickoff_time);
            document.getElementById('matchTime').textContent = kickoffTime.toLocaleTimeString([], {
                hour: '2-digit', 
                minute: '2-digit'
            });
        }
    }

    updateSummaryStats(summary) {
        document.getElementById('totalOpportunities').textContent = summary.total_opportunities;
        document.getElementById('expectedROI').textContent = `${summary.expected_roi_percent}%`;
        document.getElementById('totalStake').textContent = BettorUtils.formatCurrency(summary.total_stake_recommended);
        document.getElementById('expectedProfit').textContent = BettorUtils.formatCurrency(summary.expected_profit);
    }

    displayTopBets(topBets) {
        const container = document.getElementById('topBetsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        topBets.slice(0, 6).forEach(bet => {
            const betElement = this.createBetCard(bet, false);
            container.appendChild(betElement);
        });
    }

    displayAllBets(allBets) {
        const container = document.getElementById('allBetsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        allBets.forEach(bet => {
            const betElement = this.createBetCard(bet, true);
            container.appendChild(betElement);
        });
    }

    createBetCard(bet, detailed = false) {
        const card = document.createElement('div');
        card.className = `bet-card ${bet.confidence.toLowerCase()}-confidence`;
        card.dataset.confidence = bet.confidence.toLowerCase();
        
        const edgeColor = bet.edge_percent > 30 ? 'var(--secondary-color)' : 
                         bet.edge_percent > 15 ? 'var(--warning-color)' : 'var(--text-muted)';
        
        card.innerHTML = `
            <div class="bet-header">
                <div class="bet-player">
                    <div class="player-name">${bet.player}</div>
                    <div class="bet-market">${bet.bet_description}</div>
                </div>
                <div class="confidence-badge ${bet.confidence.toLowerCase()}">${bet.confidence}</div>
            </div>
            
            <div class="bet-details">
                <div class="bet-detail">
                    <div class="detail-value" style="color: ${edgeColor}">${bet.edge_percent}%</div>
                    <div class="detail-label">Edge</div>
                </div>
                <div class="bet-detail">
                    <div class="detail-value">${bet.odds_american}</div>
                    <div class="detail-label">Odds</div>
                </div>
                <div class="bet-detail">
                    <div class="detail-value">${bet.model_probability_percent}%</div>
                    <div class="detail-label">Model Prob</div>
                </div>
                <div class="bet-detail">
                    <div class="detail-value">${bet.kelly_percent}%</div>
                    <div class="detail-label">Kelly</div>
                </div>
            </div>
            
            <div class="bet-financial">
                <div class="stake-info">
                    <div class="stake-value">${BettorUtils.formatCurrency(bet.recommended_stake_dollars)}</div>
                    <div class="stake-label">Stake</div>
                </div>
                <div class="profit-info">
                    <div class="profit-value">${BettorUtils.formatCurrency(bet.potential_profit_dollars)}</div>
                    <div class="profit-label">Profit</div>
                </div>
            </div>
        `;
        
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

console.log('📊 Analysis JavaScript loaded');

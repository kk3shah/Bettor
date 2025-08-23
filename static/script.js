// 🎯 Bettor - Main App JavaScript

class BettorApp {
    constructor() {
        this.matches = [];
        this.selectedMatch = null;
        this.init();
    }

    init() {
        this.loadMatches();
        this.bindEvents();
        this.updateStats();
    }

    bindEvents() {
        const matchSelect = document.getElementById('matchSelect');
        const analyzeBtn = document.getElementById('analyzeBtn');

        if (matchSelect) {
            matchSelect.addEventListener('change', (e) => {
                this.handleMatchSelection(e.target.value);
            });
        }

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.analyzeMatch();
            });
        }
    }

    async loadMatches() {
        const loadingEl = document.getElementById('loading');
        const selectorEl = document.getElementById('match-selector');
        const noMatchesEl = document.getElementById('no-matches');

        try {
            console.log('🔍 Fetching upcoming matches...');
            const response = await fetch('/api/matches?hours=8');
            const matches = await response.json();

            this.matches = matches;
            
            if (matches.length === 0) {
                this.showNoMatches();
                return;
            }

            this.populateMatchDropdown(matches);
            this.showMatchSelector();

        } catch (error) {
            console.error('❌ Error loading matches:', error);
            this.showNoMatches();
        }
    }

    populateMatchDropdown(matches) {
        const matchSelect = document.getElementById('matchSelect');
        
        // Clear existing options except first
        matchSelect.innerHTML = '<option value="">Choose a match...</option>';

        matches.forEach(match => {
            const option = document.createElement('option');
            option.value = match.id;
            option.textContent = `⚽ ${match.home_team} vs ${match.away_team} | ${match.league} | ${match.kickoff} - ${match.time_until}`;
            option.dataset.homeTeam = match.home_team;
            option.dataset.awayTeam = match.away_team;
            option.dataset.kickoff = match.kickoff;
            option.dataset.timeUntil = match.time_until;
            option.dataset.league = match.league;
            option.dataset.venue = match.venue || '';
            matchSelect.appendChild(option);
        });

        console.log(`✅ Loaded ${matches.length} matches`);
    }

    handleMatchSelection(matchId) {
        const matchInfo = document.getElementById('match-info');
        
        if (!matchId) {
            matchInfo.style.display = 'none';
            this.selectedMatch = null;
            return;
        }

        const selectedOption = document.querySelector(`option[value="${matchId}"]`);
        if (!selectedOption) return;

        const match = {
            id: matchId,
            homeTeam: selectedOption.dataset.homeTeam,
            awayTeam: selectedOption.dataset.awayTeam,
            kickoff: selectedOption.dataset.kickoff,
            timeUntil: selectedOption.dataset.timeUntil
        };

        this.selectedMatch = match;
        this.displayMatchInfo(match);
        matchInfo.style.display = 'block';
    }

    displayMatchInfo(match) {
        document.getElementById('homeTeam').textContent = match.homeTeam;
        document.getElementById('awayTeam').textContent = match.awayTeam;
        document.getElementById('kickoffTime').textContent = match.kickoff;
        document.getElementById('timeUntil').textContent = match.timeUntil;
    }

    analyzeMatch() {
        if (!this.selectedMatch) return;

        const { homeTeam, awayTeam } = this.selectedMatch;
        
        // Show loading modal
        this.showAnalysisModal();
        
        // Redirect to analysis page
        setTimeout(() => {
            window.location.href = `/match/${encodeURIComponent(homeTeam)}/${encodeURIComponent(awayTeam)}`;
        }, 2000);
    }

    showAnalysisModal() {
        const modal = document.getElementById('analysisModal');
        modal.style.display = 'flex';

        // Simulate progress steps
        setTimeout(() => {
            this.activateStep('step2');
        }, 800);

        setTimeout(() => {
            this.activateStep('step3');
        }, 1500);
    }

    activateStep(stepId) {
        // Remove active class from all steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Add active class to current step
        const currentStep = document.getElementById(stepId);
        if (currentStep) {
            currentStep.classList.add('active');
        }
    }

    showMatchSelector() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('match-selector').style.display = 'block';
        document.getElementById('no-matches').style.display = 'none';
    }

    showNoMatches() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('match-selector').style.display = 'none';
        document.getElementById('no-matches').style.display = 'block';
    }

    updateStats() {
        // Update dynamic stats
        const totalMatchesEl = document.getElementById('totalMatches');
        if (totalMatchesEl) {
            // Simulate total matches analyzed
            totalMatchesEl.textContent = Math.floor(Math.random() * 100) + 150;
        }
    }

    // Utility methods
    static formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    static formatPercentage(value) {
        return `${(value * 100).toFixed(1)}%`;
    }

    static formatTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
}

// Utility functions for global use
window.BettorUtils = {
    formatCurrency: BettorApp.formatCurrency,
    formatPercentage: BettorApp.formatPercentage,
    formatTime: BettorApp.formatTime,
    
    animateValue: (element, start, end, duration = 1000) => {
        const startTimestamp = performance.now();
        
        const step = (timestamp) => {
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = start + (end - start) * progress;
            
            if (element) {
                if (element.classList.contains('currency')) {
                    element.textContent = BettorApp.formatCurrency(current);
                } else if (element.classList.contains('percentage')) {
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

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Bettor App Initializing...');
    new BettorApp();
});

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('📱 SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('❌ SW registration failed: ', registrationError);
            });
    });
}

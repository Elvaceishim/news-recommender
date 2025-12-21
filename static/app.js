// Configuration
const API_BASE = '';
const USER_ID = 1;

// Track clicked articles
const clickedArticles = new Set(
    JSON.parse(localStorage.getItem('clickedArticles') || '[]')
);

// DOM Elements
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const articlesEl = document.getElementById('articles');

// Format relative time
function formatTime(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
}

// Get source badge class
function getSourceClass(source) {
    const s = source.toLowerCase();
    if (s.includes('bbc')) return 'bbc';
    if (s.includes('nyt') || s.includes('times')) return 'nyt';
    if (s.includes('guardian')) return 'guardian';
    if (s.includes('techcrunch')) return 'techcrunch';
    if (s.includes('npr')) return 'npr';
    return '';
}

// Get short source name
function getSourceName(source) {
    if (source.toLowerCase().includes('bbc')) return 'BBC';
    if (source.toLowerCase().includes('nyt') || source.toLowerCase().includes('times')) return 'NYT';
    if (source.toLowerCase().includes('guardian')) return 'Guardian';
    if (source.toLowerCase().includes('techcrunch')) return 'TechCrunch';
    if (source.toLowerCase().includes('npr')) return 'NPR';
    return source.split('|')[0].trim().slice(0, 15);
}

const likedArticles = new Set(
    JSON.parse(localStorage.getItem('likedArticles') || '[]')
);

const dislikedArticles = new Set(
    JSON.parse(localStorage.getItem('dislikedArticles') || '[]')
);

// Create article card HTML
function createArticleCard(article) {
    const isClicked = clickedArticles.has(article.id);
    const isLiked = likedArticles.has(article.id);
    const isDisliked = dislikedArticles.has(article.id);
    const sourceClass = getSourceClass(article.source || '');
    const sourceName = getSourceName(article.source || 'Unknown');

    return `
        <article class="article-card ${isClicked ? 'clicked' : ''} ${isDisliked ? 'disliked' : ''}" 
                 data-id="${article.id}" 
                 data-link="${article.link}">
            <span class="source-badge ${sourceClass}">${sourceName}</span>
            <h2 class="article-title">${article.title}</h2>
            <div class="article-meta">
                <span class="time">${formatTime(article.published_date)}</span>
                <span class="read-more">Read</span>
            </div>
            
            <div class="article-actions">
                <button class="like-btn ${isLiked ? 'liked' : ''}" onclick="handleLike(event, ${article.id})">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="${isLiked ? '#ef4444' : 'none'}" stroke="currentColor" stroke-width="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                    ${isLiked ? 'Liked' : 'Like'}
                </button>
                <button class="dislike-btn ${isDisliked ? 'disliked' : ''}" onclick="handleDislike(event, ${article.id})">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                    </svg>
                    ${isDisliked ? 'Not for me' : 'Not interested'}
                </button>
            </div>
        </article>
    `;
}

// Load articles from API
async function loadArticles() {
    loadingEl.classList.remove('hidden');
    errorEl.classList.add('hidden');
    articlesEl.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/recommend?user_id=${USER_ID}&limit=12`);
        if (!response.ok) throw new Error('Failed to fetch');

        const articles = await response.json();
        loadingEl.classList.add('hidden');

        articlesEl.innerHTML = articles.map(createArticleCard).join('');
        attachClickHandlers();
    } catch (error) {
        console.error('Error loading articles:', error);
        loadingEl.classList.add('hidden');
        errorEl.classList.remove('hidden');
    }
}

// Log interaction to API
async function logInteraction(articleId, type = 'click') {
    try {
        await fetch(`${API_BASE}/interactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID,
                article_id: articleId,
                interaction_type: type
            })
        });
    } catch (error) {
        console.error('Error logging interaction:', error);
    }
}

// Handle Like button click
function handleLike(event, articleId) {
    event.stopPropagation(); // Prevent card click
    const card = event.currentTarget.closest('.article-card');
    const isLiked = likedArticles.has(articleId);

    // Remove dislike if exists (mutual exclusivity)
    if (dislikedArticles.has(articleId)) {
        dislikedArticles.delete(articleId);
        localStorage.setItem('dislikedArticles', JSON.stringify([...dislikedArticles]));
    }

    if (isLiked) {
        // Unlike
        likedArticles.delete(articleId);
    } else {
        // Like
        likedArticles.add(articleId);
        logInteraction(articleId, 'like');
    }

    localStorage.setItem('likedArticles', JSON.stringify([...likedArticles]));
    // Re-render the card
    loadArticles();
}

// Handle Dislike button click
function handleDislike(event, articleId) {
    event.stopPropagation(); // Prevent card click
    const isDisliked = dislikedArticles.has(articleId);

    // Remove like if exists (mutual exclusivity)
    if (likedArticles.has(articleId)) {
        likedArticles.delete(articleId);
        localStorage.setItem('likedArticles', JSON.stringify([...likedArticles]));
    }

    if (isDisliked) {
        // Un-dislike (toggle off)
        dislikedArticles.delete(articleId);
    } else {
        // Dislike
        dislikedArticles.add(articleId);
        logInteraction(articleId, 'dislike');
    }

    localStorage.setItem('dislikedArticles', JSON.stringify([...dislikedArticles]));
    // Re-render to update UI
    loadArticles();
}

// Handle article click
function handleArticleClick(event) {
    // Ignore if clicked on button (though stopPropagation should handle it)
    if (event.target.closest('button')) return;

    const card = event.currentTarget;
    const articleId = parseInt(card.dataset.id);
    const link = card.dataset.link;

    // Mark as clicked
    clickedArticles.add(articleId);
    localStorage.setItem('clickedArticles', JSON.stringify([...clickedArticles]));
    card.classList.add('clicked');

    // Log interaction
    logInteraction(articleId, 'click');

    // Open article in new tab
    window.open(link, '_blank');
}

// Attach click handlers to cards
function attachClickHandlers() {
    document.querySelectorAll('.article-card').forEach(card => {
        card.addEventListener('click', handleArticleClick);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', loadArticles);

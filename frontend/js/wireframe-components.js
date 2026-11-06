/**
 * frontend/js/wireframe-components.js
 * Comprehensive Wireframe Component Library & Visual Renderer.
 * Phase 5 — Wireframe Component Library & Renderer
 *
 * Implements standard, robust component renderers for all 32 canonical section types
 * and 8 canonical layout engine configurations with guaranteed safe fallbacks.
 */

window.WireframeComponents = (() => {
    'use strict';

    // Helper: Safely escape HTML to prevent XSS while maintaining clean markup
    function escapeHtml(str) {
        if (!str && str !== 0) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Helper: Resolve SVG or Emoji from icon library or provide safe fallback
    function getVisual(category, index = 0, explicitIcon = null) {
        if (explicitIcon) {
            if (window.WireframeIconLibrary && window.WireframeIconLibrary.svg && window.WireframeIconLibrary.svg[explicitIcon.toLowerCase()]) {
                return `<span class="wf-icon-svg">${window.WireframeIconLibrary.svg[explicitIcon.toLowerCase()]}</span>`;
            }
            return `<span class="wf-icon-emoji">${escapeHtml(explicitIcon)}</span>`;
        }
        if (window.WireframeIconLibrary && typeof window.WireframeIconLibrary.getSectionVisual === 'function') {
            const visual = window.WireframeIconLibrary.getSectionVisual(category, index);
            return visual.iconSvg ? `<span class="wf-icon-svg">${visual.iconSvg}</span>` : `<span class="wf-icon-emoji">${visual.emoji}</span>`;
        }
        return `<span class="wf-icon-emoji">✨</span>`;
    }

    // Helper: Standard Wireframe Mockup Placeholder Box
    function createMockupBox(label = 'Mockup Preview', width = '100%', height = '240px', iconName = 'image', extraClass = '') {
        const svgIcon = window.WireframeIconLibrary?.svg?.[iconName] || `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
        `;
        return `
            <div class="wf-mockup-placeholder ${extraClass}" style="width: ${width}; height: ${height};">
                <div class="wf-mockup-watermark">
                    <div class="wf-mockup-icon">${svgIcon}</div>
                    <span class="wf-mockup-label">${escapeHtml(label)}</span>
                </div>
            </div>
        `;
    }

    // Helper: Star rating display
    function renderStars(rating = 5) {
        const stars = Math.min(5, Math.max(1, Math.round(Number(rating) || 5)));
        return `<div class="wf-stars-rating" title="${stars} out of 5 stars">${'★'.repeat(stars)}${'☆'.repeat(5 - stars)}</div>`;
    }

    // =========================================================================
    // SECTION 1: NAVIGATION COMPONENTS
    // =========================================================================

    function renderNavbar(section) {
        const title = section.title && !['navbar', 'navigation bar', 'nav'].includes(section.title.toLowerCase()) ? section.title : 'Brand';
        const logoContent = section.logoUrl
            ? `<img src="${section.logoUrl}" alt="Logo" class="wf-nav-logo-img">`
            : `<span class="wf-nav-logo-text editable-text" data-field="title">${escapeHtml(title)}</span>`;

        const menuItems = Array.isArray(section.menuItems) && section.menuItems.length > 0
            ? section.menuItems
            : ['Home', 'Features', 'Products', 'Pricing', 'About', 'Contact'];

        const buttonText = section.buttonText || 'Get Started';
        const variant = (section.layoutVariant || 'layout-horizontal').toLowerCase();

        // 1. Dropdown Navigation
        if (variant === 'layout-dropdown' || variant.includes('dropdown')) {
            return `
                <div class="navbar-wireframe wf-nav-dropdown-layout">
                    <div class="wf-nav-brand">${logoContent}</div>
                    <nav class="wf-nav-links">
                        <div class="wf-dropdown-item has-dropdown">
                            <span class="nav-link">Products ▾</span>
                            <div class="wf-dropdown-menu">
                                <a href="#" class="wf-dropdown-link">
                                    <strong>Platform Core</strong>
                                    <span>High performance automation suite</span>
                                </a>
                                <a href="#" class="wf-dropdown-link">
                                    <strong>Integrations</strong>
                                    <span>Connect with 100+ native APIs</span>
                                </a>
                                <a href="#" class="wf-dropdown-link">
                                    <strong>Enterprise Suite</strong>
                                    <span>Advanced security & compliance</span>
                                </a>
                            </div>
                        </div>
                        <div class="wf-dropdown-item has-dropdown">
                            <span class="nav-link">Solutions ▾</span>
                            <div class="wf-dropdown-menu">
                                <a href="#" class="wf-dropdown-link"><strong>For Teams</strong><span>Collaborative workflows</span></a>
                                <a href="#" class="wf-dropdown-link"><strong>For Scale</strong><span>Elastic cloud architecture</span></a>
                            </div>
                        </div>
                        ${menuItems.slice(2).map(item => `<a href="#" class="nav-link">${escapeHtml(item)}</a>`).join('')}
                    </nav>
                    <div class="wf-nav-actions">
                        <button class="cta-button btn-secondary" style="margin-right: 8px;">Log In</button>
                        <button class="cta-button">${escapeHtml(buttonText)}</button>
                    </div>
                </div>
            `;
        }

        // 2. Mega Menu Navigation
        if (variant === 'layout-mega' || variant.includes('mega')) {
            return `
                <div class="navbar-wireframe wf-nav-mega-layout">
                    <div class="wf-nav-brand">${logoContent}</div>
                    <nav class="wf-nav-links">
                        <div class="wf-mega-trigger has-dropdown">
                            <span class="nav-link active">Explore Products ▾</span>
                            <div class="wf-mega-menu-flyout">
                                <div class="wf-mega-column">
                                    <h4>Design & Build</h4>
                                    <a href="#" class="wf-mega-link">⚡ Wireframe Generator</a>
                                    <a href="#" class="wf-mega-link">🎨 Component Stacks</a>
                                    <a href="#" class="wf-mega-link">📱 Responsive Engine</a>
                                </div>
                                <div class="wf-mega-column">
                                    <h4>Deployment</h4>
                                    <a href="#" class="wf-mega-link">📦 React & Tailwind Export</a>
                                    <a href="#" class="wf-mega-link">🌐 Webflow & WP JSON</a>
                                    <a href="#" class="wf-mega-link">🔒 Production Audit</a>
                                </div>
                                <div class="wf-mega-column wf-mega-featured">
                                    <span class="wf-badge">NEW</span>
                                    <h4>AI Provider Switcher</h4>
                                    <p>Seamlessly toggle between local Ollama and hosted models with zero lock-in.</p>
                                    <a href="#" class="wf-link-arrow">Learn more →</a>
                                </div>
                            </div>
                        </div>
                        ${menuItems.slice(1, 4).map(item => `<a href="#" class="nav-link">${escapeHtml(item)}</a>`).join('')}
                    </nav>
                    <div class="wf-nav-actions">
                        <button class="cta-button">${escapeHtml(buttonText)}</button>
                    </div>
                </div>
            `;
        }

        // 3. Mobile Navigation (Drawer preview)
        if (variant === 'layout-mobile' || variant === 'layout-hamburger' || variant.includes('mobile')) {
            return `
                <div class="navbar-wireframe wf-nav-mobile-layout">
                    <div class="wf-mobile-nav-bar">
                        <div class="wf-nav-brand">${logoContent}</div>
                        <button class="wf-hamburger-btn" title="Toggle navigation menu" onclick="this.closest('.navbar-wireframe').classList.toggle('drawer-open')">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="3" y1="6" x2="21" y2="6"></line>
                                <line x1="3" y1="12" x2="21" y2="12"></line>
                                <line x1="3" y1="18" x2="21" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="wf-mobile-drawer">
                        <div class="wf-mobile-search">
                            <input type="text" placeholder="Search website..." class="wf-input" readonly>
                        </div>
                        <div class="wf-mobile-links">
                            ${menuItems.map(item => `<a href="#" class="wf-mobile-link">${escapeHtml(item)}</a>`).join('')}
                        </div>
                        <div class="wf-mobile-cta">
                            <button class="cta-button wf-btn-full">${escapeHtml(buttonText)}</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // 4. Centered Logo with Split Links
        if (variant === 'layout-centered-logo' || variant.includes('centered-logo')) {
            const mid = Math.ceil(menuItems.length / 2);
            const leftLinks = menuItems.slice(0, mid);
            const rightLinks = menuItems.slice(mid);
            return `
                <div class="navbar-wireframe wf-nav-centered-logo-layout">
                    <nav class="wf-nav-links left-links">
                        ${leftLinks.map(item => `<a href="#" class="nav-link">${escapeHtml(item)}</a>`).join('')}
                    </nav>
                    <div class="wf-nav-brand center-brand">${logoContent}</div>
                    <nav class="wf-nav-links right-links">
                        ${rightLinks.map(item => `<a href="#" class="nav-link">${escapeHtml(item)}</a>`).join('')}
                        <button class="cta-button btn-sm">${escapeHtml(buttonText)}</button>
                    </nav>
                </div>
            `;
        }

        // 5. Standard Horizontal Navbar (Default)
        return `
            <div class="navbar-wireframe wf-nav-standard-layout">
                <div class="wf-nav-brand">${logoContent}</div>
                <nav class="wf-nav-links">
                    ${menuItems.map(item => `<a href="#" class="nav-link">${escapeHtml(item)}</a>`).join('')}
                </nav>
                <div class="wf-nav-actions">
                    <button class="cta-button">${escapeHtml(buttonText)}</button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // SECTION 2: HERO COMPONENTS
    // =========================================================================

    function renderHero(section) {
        const title = section.title || 'Build Faster, Smarter Digital Experiences';
        const desc = section.description || 'Transform ideas into clean, validated, responsive web architectures with intelligent design automation.';
        const buttonText = section.buttonText || 'Start Free Trial';
        const secondaryBtn = section.secondaryButtonText || 'Book a Demo';
        const type = (section.type || '').toLowerCase();
        const variant = (section.layoutVariant || 'layout-split-right').toLowerCase();

        // 1. Product Hero (SaaS / E-commerce Product Showcase)
        if (type === 'product-hero' || variant === 'layout-product' || variant.includes('product')) {
            return `
                <div class="hero-wireframe wf-hero-product">
                    <div class="wf-hero-product-details">
                        <div class="wf-pill-badge">✨ NEW GENERATION</div>
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <div class="wf-rating-row">
                            ${renderStars(5)}
                            <span class="wf-rating-count">4.9 / 5.0 (2,400+ verified customer reviews)</span>
                        </div>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-product-price-row">
                            <span class="wf-product-price">$149</span>
                            <span class="wf-product-original-price">$249</span>
                            <span class="wf-discount-badge">Save 40%</span>
                        </div>
                        <div class="wf-hero-buttons">
                            <button class="cta-button wf-btn-lg">${escapeHtml(buttonText)}</button>
                            <button class="cta-button btn-secondary wf-btn-lg">${escapeHtml(secondaryBtn)}</button>
                        </div>
                        <div class="wf-trust-perks">
                            <span>✓ Free Worldwide Shipping</span>
                            <span>✓ 30-Day Money-Back Guarantee</span>
                            <span>✓ 24/7 Dedicated Support</span>
                        </div>
                    </div>
                    <div class="wf-hero-product-media">
                        ${createMockupBox('Product 3D Showcase & UI Preview', '100%', '380px', 'sparkles', 'wf-product-media-box')}
                    </div>
                </div>
            `;
        }

        // 2. CTA Hero (High-Conversion Lead Capture)
        if (type === 'cta-hero' || variant === 'layout-cta' || variant.includes('cta')) {
            return `
                <div class="hero-wireframe wf-hero-cta">
                    <div class="wf-hero-cta-inner">
                        <div class="wf-pill-badge">⚡ INSTANT LAUNCH</div>
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-hero-email-capture">
                            <input type="email" placeholder="Enter your work email address..." class="wf-input wf-input-lg" readonly>
                            <button class="cta-button wf-btn-lg">${escapeHtml(buttonText)}</button>
                        </div>
                        <div class="wf-hero-security-badges">
                            <span>🔒 SOC-2 Type II Certified</span>
                            <span>🛡️ GDPR & CCPA Compliant</span>
                            <span>⚡ 99.99% Guaranteed SLA</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // 3. Centered Hero
        if (variant === 'layout-centered' || variant === 'centered') {
            return `
                <div class="hero-wireframe layout-centered wf-hero-centered">
                    <div class="hero-text">
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-hero-buttons">
                            <button class="cta-button">${escapeHtml(buttonText)}</button>
                            <button class="cta-button btn-secondary">${escapeHtml(secondaryBtn)}</button>
                        </div>
                    </div>
                    <div class="hero-image-full" style="margin-top: 32px;">
                        ${createMockupBox('Application Dashboard Mockup', '100%', '360px', 'chart')}
                    </div>
                </div>
            `;
        }

        // 4. Image Background / Full Bleed Hero
        if (variant === 'layout-full-bg' || variant.includes('full-bg')) {
            return `
                <div class="hero-wireframe layout-full-bg wf-hero-full-bg">
                    <div class="wf-hero-bg-overlay"></div>
                    <div class="hero-text wf-hero-overlay-content">
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-hero-buttons">
                            <button class="cta-button wf-btn-lg">${escapeHtml(buttonText)}</button>
                            <button class="cta-button btn-secondary wf-btn-lg">${escapeHtml(secondaryBtn)}</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // 5. Asymmetric Layout Hero
        if (variant === 'layout-asymmetric' || variant.includes('asymmetric')) {
            return `
                <div class="hero-wireframe layout-asymmetric wf-hero-asymmetric">
                    <div class="hero-text">
                        <div class="wf-pill-badge">🚀 ACCELERATED WORKFLOWS</div>
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-hero-buttons">
                            <button class="cta-button">${escapeHtml(buttonText)}</button>
                        </div>
                    </div>
                    <div class="hero-image">
                        ${createMockupBox('Interactive Workspace Preview', '100%', '340px', 'lightning', 'wf-tilted-mockup')}
                    </div>
                </div>
            `;
        }

        // 6. Split Left Hero
        if (variant === 'layout-split-left' || variant === 'split-left') {
            return `
                <div class="hero-wireframe layout-split-left wf-hero-split">
                    <div class="hero-image">
                        ${createMockupBox('Visual Experience Mockup', '100%', '320px', 'image')}
                    </div>
                    <div class="hero-text">
                        <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                        <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                        <div class="wf-hero-buttons">
                            <button class="cta-button">${escapeHtml(buttonText)}</button>
                            <button class="cta-button btn-secondary">${escapeHtml(secondaryBtn)}</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // 7. Split Right Hero (Default)
        return `
            <div class="hero-wireframe layout-split-right wf-hero-split">
                <div class="hero-text">
                    <h1 class="editable-text" data-field="title">${escapeHtml(title)}</h1>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                    <div class="wf-hero-buttons">
                        <button class="cta-button">${escapeHtml(buttonText)}</button>
                        <button class="cta-button btn-secondary">${escapeHtml(secondaryBtn)}</button>
                    </div>
                </div>
                <div class="hero-image">
                    ${createMockupBox('Product Platform Interface', '100%', '320px', 'sparkles')}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // SECTION 3: CONTENT COMPONENTS
    // =========================================================================

    // 1. About Section & Brand Story
    function renderAbout(section, variant = 'layout-split') {
        const title = section.title || 'About Our Mission & Values';
        const desc = section.description || 'Founded with the conviction that great technology should empower creativity, we build software that connects design directly to reality.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: '12+', desc: 'Years Experience' },
            { title: '99.9%', desc: 'Platform Uptime' },
            { title: '400k+', desc: 'Active Projects' }
        ];

        return `
            <div class="wf-about-section ${variant}">
                <div class="wf-about-text">
                    <div class="wf-pill-badge">WHO WE ARE</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                    <div class="wf-about-stats-row">
                        ${items.slice(0, 3).map((item, i) => `
                            <div class="wf-about-stat-item">
                                <div class="wf-about-stat-num editable-text" data-field="item-title" data-index="${i}">${escapeHtml(item.title || item.value || '10+')}</div>
                                <div class="wf-about-stat-label editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(item.desc || item.label || 'Years')}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="wf-about-media">
                    ${createMockupBox('Team & Culture Visual', '100%', '320px', 'user')}
                </div>
            </div>
        `;
    }

    // 2. Image and Text Alternating Section
    function renderImageText(section, variant = 'layout-split') {
        const title = section.title || 'Transforming Concepts into Execution';
        const desc = section.description || 'Everything you need to deliver high-converting digital products faster, with automated workflows and complete precision.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Real-Time Sync', desc: 'Edits propagate seamlessly across canvas and code.' },
            { title: 'Enterprise Security', desc: 'Encrypted at rest, sanitized secrets, no data leaks.' },
            { title: 'Multi-Framework Output', desc: 'Deploy directly to Tailwind React, Webflow, or Elementor.' }
        ];

        return `
            <div class="wf-image-text-section ${variant}">
                <div class="wf-image-text-media">
                    ${createMockupBox('Architecture Showcase', '100%', '300px', 'chart')}
                </div>
                <div class="wf-image-text-content">
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                    <ul class="wf-checklist">
                        ${items.map((item, i) => `
                            <li>
                                <strong>✓ ${escapeHtml(item.title || `Capability ${i + 1}`)}:</strong>
                                <span>${escapeHtml(item.desc || 'Optimized performance and clarity.')}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    // 3. Feature Grid
    function renderFeatures(section, variant = 'layout-grid-3') {
        const title = section.title || 'Engineered for Performance and Scale';
        const desc = section.description || 'Discover a comprehensive set of features engineered to accelerate your development lifecycle.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Intelligent Generators', desc: 'Leverage state-of-the-art AI models for instant wireframing.' },
            { title: 'Component Library', desc: 'Over 30 canonical, responsive, accessible components.' },
            { title: 'Self-Healing JSON', desc: 'Automatic repair engine guarantees zero syntax crashes.' },
            { title: 'Multi-Device Previews', desc: 'Real-time responsive previews for desktop, tablet, and mobile.' },
            { title: 'Zero Vendor Lock-In', desc: 'Easily export production React and standard CSS.' },
            { title: 'Extensible Architecture', desc: 'Seamlessly add custom layout engines and themes.' }
        ];

        let gridClass = 'wf-grid-3';
        if (variant.includes('grid-2')) gridClass = 'wf-grid-2';
        else if (variant.includes('grid-4')) gridClass = 'wf-grid-4';
        else if (variant.includes('bento')) gridClass = 'wf-grid-bento';
        else if (variant.includes('list')) gridClass = 'wf-grid-list';

        return `
            <div class="wf-features-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">CORE CAPABILITIES</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-features-grid ${gridClass}">
                    ${items.map((item, i) => `
                        <div class="wf-feature-card" data-index="${i}">
                            <div class="wf-feature-icon-wrapper">
                                ${getVisual('features', i, item.icon)}
                            </div>
                            <h3 class="editable-text" data-field="item-title" data-index="${i}">${escapeHtml(item.title || `Feature ${i + 1}`)}</h3>
                            <p class="editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(item.desc || item.description || 'Feature description.')}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 4. Service Cards
    function renderServices(section, variant = 'layout-grid-3') {
        const title = section.title || 'Our Professional Services';
        const desc = section.description || 'Tailored design and engineering consulting services to help you build world-class digital applications.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Design Automation', desc: 'Custom pipeline implementation for generative UI workflows.', price: 'From $2,500' },
            { title: 'Architecture Review', desc: 'Comprehensive codebase and AI provider security audit.', price: 'From $1,800' },
            { title: 'Custom Components', desc: 'High-fidelity bespoke React and Webflow design libraries.', price: 'From $3,200' }
        ];

        return `
            <div class="wf-services-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">WHAT WE OFFER</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-services-grid wf-grid-3">
                    ${items.map((service, i) => `
                        <div class="wf-service-card" data-index="${i}">
                            <div class="wf-service-icon">${getVisual('services', i, service.icon)}</div>
                            <h3 class="editable-text" data-field="item-title" data-index="${i}">${escapeHtml(service.title || `Service ${i + 1}`)}</h3>
                            <p class="editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(service.desc || service.description || 'Service details.')}</p>
                            ${service.price ? `<div class="wf-service-price">${escapeHtml(service.price)}</div>` : ''}
                            <button class="cta-button btn-secondary wf-btn-sm" style="margin-top: 16px;">Learn More →</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 5. Product Grid (E-commerce catalog)
    function renderProductGrid(section, variant = 'layout-grid-4') {
        const title = section.title || 'Featured Products & Catalog';
        const desc = section.description || 'Explore our top-selling items with verified quality and instant delivery.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Wireless Pro Headset', price: '$129', rating: 5, tag: 'BESTSELLER' },
            { title: 'Ergonomic Desk Hub', price: '$89', rating: 5, tag: 'NEW' },
            { title: 'Precision Touch Controller', price: '$149', rating: 4, tag: 'SALE' },
            { title: 'Ultra-Fast Charging Mat', price: '$49', rating: 5, tag: '' }
        ];

        return `
            <div class="wf-product-grid-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">STORE CATALOG</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-products-grid wf-grid-4">
                    ${items.map((prod, i) => `
                        <div class="wf-product-card" data-index="${i}">
                            <div class="wf-product-thumb">
                                ${prod.tag ? `<span class="wf-product-badge">${escapeHtml(prod.tag)}</span>` : ''}
                                ${createMockupBox(prod.title || 'Product Photo', '100%', '180px', 'image', 'wf-product-mockup')}
                            </div>
                            <div class="wf-product-body">
                                <div class="wf-product-rating">${renderStars(prod.rating || 5)}</div>
                                <h4 class="wf-product-title editable-text" data-field="item-title" data-index="${i}">${escapeHtml(prod.title || `Product ${i + 1}`)}</h4>
                                <div class="wf-product-price-bar">
                                    <span class="wf-product-card-price">${escapeHtml(prod.price || '$99')}</span>
                                    <button class="cta-button btn-sm">Add to Cart</button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 6. Statistics Section
    function renderStats(section, variant = 'layout-grid-4') {
        const title = section.title || 'Proven Track Record of Excellence';
        const desc = section.description || 'Numbers that showcase our commitment to reliability, speed, and customer satisfaction.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: '99.99%', desc: 'Guaranteed System Uptime' },
            { title: '250M+', desc: 'Requests Processed Daily' },
            { title: '< 15ms', desc: 'Average Edge Latency' },
            { title: '4.98★', desc: 'Average Enterprise Rating' }
        ];

        return `
            <div class="wf-stats-section">
                <div class="wf-section-header">
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-stats-grid wf-grid-4">
                    ${items.map((stat, i) => `
                        <div class="wf-stat-card" data-index="${i}">
                            <div class="wf-stat-value editable-text" data-field="item-title" data-index="${i}">${escapeHtml(stat.title || stat.value || '100+')}</div>
                            <div class="wf-stat-label editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(stat.desc || stat.label || 'Metric')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 7. Testimonials Section
    function renderTestimonials(section, variant = 'layout-grid-3') {
        const title = section.title || 'Loved by Thousands of Modern Teams';
        const desc = section.description || 'See what founders, architects, and engineering leaders say about their experience.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            {
                quote: 'This platform saved our design and frontend team over 200 hours during our initial product launch.',
                name: 'Sarah Jenkins',
                role: 'Head of Product, TechFlow Inc.'
            },
            {
                quote: 'The export quality into clean React and Tailwind code is unparalleled. No cleanup required.',
                name: 'David Chen',
                role: 'Principal Architect, CloudScale'
            },
            {
                quote: 'Having true offline local AI support with Ollama gives our compliance team peace of mind.',
                name: 'Elena Rostova',
                role: 'VP of Engineering, DataCore'
            }
        ];

        return `
            <div class="wf-testimonials-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">CLIENT STORIES</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-testimonials-grid wf-grid-3">
                    ${items.map((t, i) => `
                        <div class="wf-testimonial-card" data-index="${i}">
                            <div class="wf-testimonial-stars">${renderStars(5)}</div>
                            <blockquote class="wf-testimonial-quote editable-text" data-field="item-desc" data-index="${i}">
                                "${escapeHtml(t.quote || t.desc || 'Outstanding performance and reliability.')}"
                            </blockquote>
                            <div class="wf-testimonial-author">
                                <div class="wf-avatar-circle">${escapeHtml((t.name || 'User')[0])}</div>
                                <div class="wf-author-meta">
                                    <div class="wf-author-name editable-text" data-field="item-title" data-index="${i}">${escapeHtml(t.name || t.title || 'Client Name')}</div>
                                    <div class="wf-author-role">${escapeHtml(t.role || 'Enterprise Customer')}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 8. Team Section
    function renderTeam(section, variant = 'layout-grid-3') {
        const title = section.title || 'Meet the Minds Behind the Mission';
        const desc = section.description || 'A passionate team of designers, AI researchers, and engineers building the future of software creation.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { name: 'Alex Morgan', role: 'Founder & CEO', desc: 'Former Design Lead at Stripe with 15+ years experience.' },
            { name: 'Dr. Priya Patel', role: 'Head of AI Engineering', desc: 'PhD in NLP & Machine Learning; specialist in LLM reasoning.' },
            { name: 'Marcus Bell', role: 'Chief Product Architect', desc: 'Architect of high-scale enterprise frontend component systems.' }
        ];

        return `
            <div class="wf-team-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">OUR LEADERSHIP</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-team-grid wf-grid-3">
                    ${items.map((member, i) => `
                        <div class="wf-team-card" data-index="${i}">
                            <div class="wf-team-photo-wrap">
                                ${createMockupBox(member.name || 'Member Photo', '100%', '200px', 'user', 'wf-team-photo')}
                            </div>
                            <h3 class="wf-team-name editable-text" data-field="item-title" data-index="${i}">${escapeHtml(member.name || member.title || `Member ${i + 1}`)}</h3>
                            <div class="wf-team-role">${escapeHtml(member.role || 'Core Team')}</div>
                            <p class="wf-team-bio editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(member.desc || member.description || 'Dedicated to customer success.')}</p>
                            <div class="wf-team-socials">
                                <span>LinkedIn</span> • <span>Twitter</span> • <span>GitHub</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 9. Gallery Section
    function renderGallery(section, variant = 'layout-grid-3') {
        const title = section.title || 'Project Visual Showcase';
        const desc = section.description || 'Explore our latest design concepts, design system components, and product screenshots.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Design System Kit' },
            { title: 'Mobile Analytics Suite' },
            { title: 'Enterprise Admin Board' },
            { title: 'E-commerce Checkout' },
            { title: 'Marketing Landing Page' },
            { title: 'Dark Mode Workspace' }
        ];

        return `
            <div class="wf-gallery-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">PORTFOLIO</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-gallery-grid wf-grid-3">
                    ${items.map((item, i) => `
                        <div class="wf-gallery-item" data-index="${i}">
                            ${createMockupBox(item.title || `Project View ${i + 1}`, '100%', '220px', 'image', 'wf-gallery-mockup')}
                            <div class="wf-gallery-caption">
                                <span class="editable-text" data-field="item-title" data-index="${i}">${escapeHtml(item.title || `Visual ${i + 1}`)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 10. Pricing Section
    function renderPricing(section, variant = 'layout-grid-3') {
        const title = section.title || 'Simple, Transparent, Predictable Pricing';
        const desc = section.description || 'No hidden fees. Choose the ideal plan for your project and scale seamlessly.';
        const plans = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            {
                title: 'Starter',
                price: '$29',
                desc: 'Perfect for individual creators and early stage projects.',
                features: ['Up to 5 active sitemaps', 'Standard wireframe generator', 'React & Tailwind export', 'Community support'],
                tag: ''
            },
            {
                title: 'Professional',
                price: '$79',
                desc: 'For fast-moving teams that need scale and multi-model AI.',
                features: ['Unlimited sitemaps & wireframes', 'Local Ollama & OpenRouter support', 'Webflow & Elementor JSON exports', 'Priority response queue', 'Full component editing'],
                tag: 'POPULAR'
            },
            {
                title: 'Enterprise',
                price: '$199',
                desc: 'Dedicated infrastructure, custom models, and enterprise SLAs.',
                features: ['Private model deployment', 'Custom design systems', 'Role-based team permissions', 'Dedicated technical support', '99.99% uptime agreement'],
                tag: ''
            }
        ];

        return `
            <div class="wf-pricing-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">PLANS & PACKAGES</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                    <div class="wf-billing-toggle">
                        <span class="active">Monthly Billing</span>
                        <span class="wf-toggle-switch"></span>
                        <span>Annual Billing <strong class="wf-highlight-tag">Save 20%</strong></span>
                    </div>
                </div>
                <div class="wf-pricing-grid wf-grid-3">
                    ${plans.map((plan, i) => {
                        const features = Array.isArray(plan.features) ? plan.features : (String(plan.desc || '').split(/,|\n/).filter(Boolean));
                        const isPop = plan.tag === 'POPULAR' || i === 1;
                        return `
                            <div class="wf-pricing-card ${isPop ? 'is-popular' : ''}" data-index="${i}">
                                ${isPop ? `<div class="wf-popular-ribbon">MOST POPULAR</div>` : ''}
                                <h3 class="wf-plan-title editable-text" data-field="item-title" data-index="${i}">${escapeHtml(plan.title || `Plan ${i + 1}`)}</h3>
                                <p class="wf-plan-desc">${escapeHtml(plan.desc || 'Plan details.')}</p>
                                <div class="wf-plan-price-wrap">
                                    <span class="wf-plan-currency">$</span>
                                    <span class="wf-plan-price">${escapeHtml((plan.price || '$49').replace('$', ''))}</span>
                                    <span class="wf-plan-period">/ month</span>
                                </div>
                                <ul class="wf-plan-features">
                                    ${features.map(f => `<li><span class="wf-check-icon">✓</span> ${escapeHtml(f)}</li>`).join('')}
                                </ul>
                                <button class="cta-button wf-btn-full ${isPop ? '' : 'btn-secondary'}">
                                    ${escapeHtml(section.buttonText || (isPop ? 'Get Started' : 'Choose Plan'))}
                                </button>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // 11. FAQ Section (Accordion)
    function renderFAQ(section, variant = 'layout-default') {
        const title = section.title || 'Frequently Asked Questions';
        const desc = section.description || 'Have questions? Here are quick answers to the most common inquiries about our platform.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            {
                title: 'Can I run wireframe models locally without sending data to the cloud?',
                desc: 'Yes! The platform natively supports Ollama for local execution on your GPU/CPU, ensuring complete offline privacy.'
            },
            {
                title: 'What export formats are supported out of the box?',
                desc: 'You can export production React components with Tailwind CSS v4, WordPress Elementor canvas templates, and Webflow JSON structures.'
            },
            {
                title: 'Can I regenerate individual sections without modifying the rest of my page?',
                desc: 'Absolutely. Every section has an individual regeneration trigger that preserves existing customized sections.'
            },
            {
                title: 'Is there a limit on the number of pages in a sitemap?',
                desc: 'No, the hierarchical sitemap generator supports multi-level parent/child pages across all industry categories.'
            }
        ];

        return `
            <div class="wf-faq-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">GOT QUESTIONS?</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-faq-accordion-container">
                    ${items.map((item, i) => `
                        <div class="wf-faq-item ${i === 0 ? 'is-open' : ''}" onclick="this.classList.toggle('is-open')">
                            <div class="wf-faq-question">
                                <h4 class="editable-text" data-field="item-title" data-index="${i}">${escapeHtml(item.title || item.question || `Question ${i + 1}`)}</h4>
                                <span class="wf-faq-chevron">▾</span>
                            </div>
                            <div class="wf-faq-answer">
                                <p class="editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(item.desc || item.answer || 'Answer details.')}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="wf-faq-footer-card">
                    <h4>Still have questions?</h4>
                    <p>Can’t find the answer you’re looking for? Reach out to our friendly technical support team.</p>
                    <button class="cta-button btn-secondary">Contact Support</button>
                </div>
            </div>
        `;
    }

    // 12. Blog & Articles Grid
    function renderBlog(section, variant = 'layout-grid-3') {
        const title = section.title || 'Latest Insights & Articles';
        const desc = section.description || 'Stay up to date with the latest architectural patterns, design tips, and engineering breakthroughs.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Best Practices for Local LLM Wireframing', date: 'October 14, 2026', tag: 'Engineering', desc: 'How to optimize parameter configurations for structured JSON generation.' },
            { title: 'Tailwind CSS v4 Migration Guide', date: 'September 28, 2026', tag: 'Frontend', desc: 'Understanding CSS-based configurations and modern directive handling.' },
            { title: 'Scaling Design Systems Across Multi-Page Apps', date: 'September 12, 2026', tag: 'Architecture', desc: 'Maintaining consistent design tokens, fonts, and responsive grids.' }
        ];

        return `
            <div class="wf-blog-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">KNOWLEDGE BASE</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-blog-grid wf-grid-3">
                    ${items.map((post, i) => `
                        <div class="wf-blog-card" data-index="${i}">
                            ${createMockupBox(post.title || 'Article Cover', '100%', '160px', 'image', 'wf-blog-mockup')}
                            <div class="wf-blog-card-body">
                                <div class="wf-blog-meta">
                                    <span class="wf-blog-tag">${escapeHtml(post.tag || 'Tech')}</span>
                                    <span class="wf-blog-date">${escapeHtml(post.date || 'Recent')}</span>
                                </div>
                                <h3 class="wf-blog-title editable-text" data-field="item-title" data-index="${i}">${escapeHtml(post.title || `Post ${i + 1}`)}</h3>
                                <p class="wf-blog-desc editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(post.desc || post.description || 'Article summary.')}</p>
                                <a href="#" class="wf-link-arrow">Read Article →</a>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 13. Contact Section (Form + Information + Map)
    function renderContact(section, variant = 'layout-split') {
        const title = section.title || 'Let’s Start a Conversation';
        const desc = section.description || 'Our team is ready to answer questions, guide your implementation, and build your digital solution.';
        const buttonText = section.buttonText || 'Send Message';

        return `
            <div class="wf-contact-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">GET IN TOUCH</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-contact-container">
                    <div class="wf-contact-form-panel">
                        <div class="wf-form-row">
                            <div class="wf-form-group">
                                <label>First Name</label>
                                <input type="text" placeholder="John" class="wf-input" readonly>
                            </div>
                            <div class="wf-form-group">
                                <label>Last Name</label>
                                <input type="text" placeholder="Doe" class="wf-input" readonly>
                            </div>
                        </div>
                        <div class="wf-form-group">
                            <label>Work Email</label>
                            <input type="email" placeholder="john@company.com" class="wf-input" readonly>
                        </div>
                        <div class="wf-form-group">
                            <label>Project Scope or Requirements</label>
                            <textarea rows="4" placeholder="Tell us about your project goals, timeline, and requirements..." class="wf-input" readonly></textarea>
                        </div>
                        <button class="cta-button wf-btn-full">${escapeHtml(buttonText)}</button>
                    </div>
                    <div class="wf-contact-info-panel">
                        <div class="wf-contact-card">
                            <div class="wf-contact-card-icon">📞</div>
                            <div>
                                <h4>Phone Inquiries</h4>
                                <p>+1 (800) 555-0199 • Mon-Fri 9am-6pm EST</p>
                            </div>
                        </div>
                        <div class="wf-contact-card">
                            <div class="wf-contact-card-icon">✉️</div>
                            <div>
                                <h4>Email Support</h4>
                                <p>support@company.com • 24/7 Response SLA</p>
                            </div>
                        </div>
                        <div class="wf-contact-card">
                            <div class="wf-contact-card-icon">📍</div>
                            <div>
                                <h4>Headquarters</h4>
                                <p>100 Innovation Way, Suite 400, San Francisco, CA</p>
                            </div>
                        </div>
                        ${createMockupBox('Interactive Map Location', '100%', '160px', 'mapPin', 'wf-contact-map')}
                    </div>
                </div>
            </div>
        `;
    }

    // 14. Step-by-Step Process / How It Works
    function renderProcess(section, variant = 'layout-grid-4') {
        const title = section.title || 'How It Works in 4 Simple Steps';
        const desc = section.description || 'From raw prompt to validated, editable multi-page wireframes in minutes.';
        const items = Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: '1. Enter Project Brief', desc: 'Provide website objectives, target audience, and preferred visual style.' },
            { title: '2. Generate Sitemap', desc: 'AI analyzes requirements and constructs a hierarchical sitemap tree.' },
            { title: '3. Plan & Build Wireframes', desc: 'Pydantic engine validates section components and layout rules.' },
            { title: '4. Customize & Export', desc: 'Edit components on the visual canvas and export production code.' }
        ];

        return `
            <div class="wf-process-section">
                <div class="wf-section-header">
                    <div class="wf-pill-badge">THE WORKFLOW</div>
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                </div>
                <div class="wf-process-grid wf-grid-4">
                    ${items.map((step, i) => `
                        <div class="wf-process-step" data-index="${i}">
                            <div class="wf-step-number-bubble">${i + 1}</div>
                            <h3 class="wf-step-title editable-text" data-field="item-title" data-index="${i}">${escapeHtml(step.title || `Step ${i + 1}`)}</h3>
                            <p class="wf-step-desc editable-text" data-field="item-desc" data-index="${i}">${escapeHtml(step.desc || step.description || 'Step details.')}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 15. Call To Action (High impact banner)
    function renderCTA(section, variant = 'layout-centered') {
        const title = section.title || 'Ready to Accelerate Your Website Design Workflow?';
        const desc = section.description || 'Join thousands of developers and product teams building higher-converting wireframes today.';
        const buttonText = section.buttonText || 'Get Started Now';

        return `
            <div class="wf-cta-banner">
                <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                <div class="wf-hero-buttons">
                    <button class="cta-button wf-btn-lg">${escapeHtml(buttonText)}</button>
                    <button class="cta-button btn-secondary wf-btn-lg">Talk to Sales</button>
                </div>
            </div>
        `;
    }

    // 16. Footer Section
    function renderFooter(section, variant = 'layout-default') {
        const title = section.title && !['footer', 'site-footer', 'bottom'].includes(section.title.toLowerCase()) ? section.title : 'Brand Inc.';
        const copyright = '© 2026 ' + escapeHtml(title) + '. All rights reserved.';
        const columns = [
            { title: 'Product', links: ['Wireframe Engine', 'Sitemap Tree', 'React Exporter', 'Tailwind v4 Kit', 'Local AI Ollama'] },
            { title: 'Solutions', links: ['For SaaS Startups', 'For Digital Agencies', 'For E-commerce', 'For Enterprise', 'Case Studies'] },
            { title: 'Resources', links: ['Documentation', 'API Reference', 'Schema Specifications', 'System Changelog', 'Community Discord'] },
            { title: 'Company', links: ['About Us', 'Careers', 'Privacy Policy', 'Terms of Service', 'Security Overview'] }
        ];

        return `
            <footer class="wf-footer-section">
                <div class="wf-footer-top-grid">
                    <div class="wf-footer-brand-col">
                        <h3 class="wf-footer-brand editable-text" data-field="title">${escapeHtml(title)}</h3>
                        <p class="wf-footer-tagline">Empowering teams with autonomous, intelligent website wireframing and design systems.</p>
                        <div class="wf-newsletter-box">
                            <label>Subscribe to product updates</label>
                            <div class="wf-newsletter-form">
                                <input type="email" placeholder="Your email address" class="wf-input" readonly>
                                <button class="cta-button btn-sm">Join</button>
                            </div>
                        </div>
                    </div>
                    ${columns.map(col => `
                        <div class="wf-footer-col">
                            <h4 class="wf-footer-col-title">${escapeHtml(col.title)}</h4>
                            <ul class="wf-footer-links">
                                ${col.links.map(link => `<li><a href="#">${escapeHtml(link)}</a></li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
                <div class="wf-footer-bottom-bar">
                    <span class="wf-copyright">${copyright}</span>
                    <div class="wf-footer-bottom-links">
                        <a href="#">Privacy</a>
                        <a href="#">Terms</a>
                        <a href="#">Cookies</a>
                        <a href="#">Security</a>
                    </div>
                </div>
            </footer>
        `;
    }

    // 17. Sidebar Content Layout
    function renderSidebarLayout(section) {
        const title = section.title || 'Main Editorial Content';
        const desc = section.description || 'Articles, detailed specifications, and primary workspace documentation.';

        return `
            <div class="wf-sidebar-layout-container">
                <div class="wf-main-content-column">
                    <h2 class="editable-text" data-field="title">${escapeHtml(title)}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(desc)}</p>
                    ${createMockupBox('Featured Article Visual', '100%', '260px', 'image')}
                    <div class="wf-prose-block">
                        <p>Modern web engineering requires seamless communication between architecture, design systems, and automated code generation. By formalizing JSON schemas, we ensure deterministic UI fidelity across all devices.</p>
                    </div>
                </div>
                <aside class="wf-aside-column">
                    <div class="wf-sidebar-widget">
                        <h4>Search Documentation</h4>
                        <input type="text" placeholder="Search topics..." class="wf-input" readonly>
                    </div>
                    <div class="wf-sidebar-widget">
                        <h4>Categories</h4>
                        <ul class="wf-sidebar-list">
                            <li><a href="#">Architecture (12)</a></li>
                            <li><a href="#">Component Specs (32)</a></li>
                            <li><a href="#">AI Providers (4)</a></li>
                            <li><a href="#">Export Pipelines (5)</a></li>
                        </ul>
                    </div>
                    <div class="wf-sidebar-widget wf-promo-widget">
                        <h4>Need Enterprise Support?</h4>
                        <p>Speak directly with our engineering core team.</p>
                        <button class="cta-button wf-btn-full">Schedule Call</button>
                    </div>
                </aside>
            </div>
        `;
    }

    // =========================================================================
    // SECTION 4: MASTER COMPONENT DISPATCHER
    // =========================================================================

    function renderComponent(section) {
        if (!section || typeof section !== 'object') {
            return `<div class="wf-error-box">Invalid section data provided.</div>`;
        }

        const type = String(section.type || 'content').toLowerCase().trim();
        const title = String(section.title || '').toLowerCase().trim();
        const variant = String(section.layoutVariant || 'layout-default').toLowerCase().trim();

        // 1. Navigation
        if (type === 'navbar' || title.includes('navbar') || title.includes('nav bar') || title === 'navigation') {
            return renderNavbar(section);
        }

        // 2. Hero Variants
        if (type === 'hero' || type === 'product-hero' || type === 'cta-hero' || title.includes('hero') || title.includes('welcome')) {
            return renderHero(section);
        }

        // 3. Features
        if (type === 'features' || type === 'key-features' || title.includes('feature')) {
            return renderFeatures(section, variant);
        }

        // 4. Services
        if (type === 'services' || type === 'services-grid' || type === 'service' || title.includes('service')) {
            return renderServices(section, variant);
        }

        // 5. Product Catalog & Commerce Grid
        if (type === 'product-grid' || type === 'products' || title.includes('product') || title.includes('catalog') || title.includes('shop')) {
            return renderProductGrid(section, variant);
        }

        // 6. Testimonials & Social Proof
        if (type === 'testimonial' || type === 'testimonials' || title.includes('testimonial') || title.includes('review')) {
            return renderTestimonials(section, variant);
        }

        // 7. Statistics & Metrics
        if (type === 'stats' || type === 'statistics' || title.includes('stats') || title.includes('impact') || title.includes('numbers')) {
            return renderStats(section, variant);
        }

        // 8. Team
        if (type === 'team' || title.includes('team') || title.includes('staff') || title.includes('leadership')) {
            return renderTeam(section, variant);
        }

        // 9. Gallery
        if (type === 'gallery' || title.includes('gallery') || title.includes('portfolio') || title.includes('showcase')) {
            return renderGallery(section, variant);
        }

        // 10. Pricing
        if (type === 'pricing' || type === 'pricing-table' || title.includes('pricing') || title.includes('plan')) {
            return renderPricing(section, variant);
        }

        // 11. FAQ
        if (type === 'faq' || title.includes('faq') || title.includes('frequently asked') || title.includes('questions')) {
            return renderFAQ(section, variant);
        }

        // 12. Blog & Articles
        if (type === 'blog' || type === 'blog-grid' || type === 'articles' || title.includes('blog') || title.includes('article') || title.includes('news')) {
            return renderBlog(section, variant);
        }

        // 13. Contact & Maps
        if (type === 'contact' || type === 'contact-form' || type === 'contact-details' || type === 'location' || title.includes('contact') || title.includes('get in touch') || title.includes('location')) {
            return renderContact(section, variant);
        }

        // 14. Process & Workflow
        if (type === 'process' || type === 'how-it-works' || title.includes('how it works') || title.includes('process') || title.includes('steps')) {
            return renderProcess(section, variant);
        }

        // 15. Call To Action (CTA)
        if (type === 'cta' || title.includes('call to action') || title.includes('ready to get started')) {
            return renderCTA(section, variant);
        }

        // 16. About & Story
        if (type === 'about' || type === 'story' || title.includes('about') || title.includes('our story')) {
            return renderAbout(section, variant);
        }

        // 17. Sidebar Layout
        if (variant === 'layout-sidebar' || variant.includes('sidebar')) {
            return renderSidebarLayout(section);
        }

        // 18. Footer
        if (type === 'footer' || title.includes('footer')) {
            return renderFooter(section, variant);
        }

        // 19. Image and Text
        if (type === 'image-text' || variant === 'layout-split') {
            return renderImageText(section, variant);
        }

        // 20. Generic & Safe Fallback
        return `
            <div class="generic-wireframe layout-default">
                <div class="wf-section-header">
                    <h2 class="editable-text" data-field="title">${escapeHtml(section.title || 'Structured Section')}</h2>
                    <p class="editable-text" data-field="description">${escapeHtml(section.description || 'Section content generated by the AI platform.')}</p>
                </div>
                ${Array.isArray(section.items) && section.items.length > 0 ? `
                    <div class="wf-generic-items-grid wf-grid-3">
                        ${section.items.map((item, i) => `
                            <div class="wf-feature-card">
                                <h4>${escapeHtml(item.title || `Item ${i + 1}`)}</h4>
                                <p>${escapeHtml(item.desc || item.description || '')}</p>
                            </div>
                        `).join('')}
                    </div>
                ` : createMockupBox('Content Layout Mockup', '100%', '200px')}
            </div>
        `;
    }

    // Public API
    return {
        escapeHtml,
        getVisual,
        createMockupBox,
        renderStars,
        renderNavbar,
        renderHero,
        renderAbout,
        renderImageText,
        renderFeatures,
        renderServices,
        renderProductGrid,
        renderStats,
        renderTestimonials,
        renderTeam,
        renderGallery,
        renderPricing,
        renderFAQ,
        renderBlog,
        renderContact,
        renderProcess,
        renderCTA,
        renderFooter,
        renderSidebarLayout,
        renderComponent
    };
})();


console.log('🚀 Website Design Automation - Updated Version 20241226');
console.log('✅ Changes loaded: Hierarchical Layout, Delete Button Position, Navigation Fix');
console.log('🔄 Two-way sync system initialized');

class SitemapApp {
    constructor() {
        this.currentSitemap = null;
        this.apiBaseUrl = '/api';
        this.activeTab = 'sitemap';
        this.currentInsertPosition = -1;
        this.currentPageId = null;
        this.currentMode = 'section';
        this.autoFitSitemap = true;
        this.lastSitemapContainer = null;
        this.lastSitemapDiv = null;
        this.lastSitemapWrapper = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupStateSync();
        window.addEventListener('resize', () => {
            if (this.lastSitemapContainer && this.lastSitemapDiv && this.lastSitemapWrapper) {
                this.fitSitemapToViewport(this.lastSitemapContainer, this.lastSitemapDiv, this.lastSitemapWrapper);
            }
        });

        // Check if we should go directly to editor (from wireframe navigation)
        if (window.location.hash === '#editor') {
            const savedSitemap = localStorage.getItem('currentSitemap');
            if (savedSitemap) {
                try {
                    this.currentSitemap = JSON.parse(savedSitemap);
                    this.showEditorPage();
                    this.renderSitemap();
                    this.updateJsonDisplay();
                    this.updatePageCount();
                    this.enableControls();
                    this.updateStatus('Ready');
                    return;
                } catch (e) {
                    console.error('Failed to restore sitemap state:', e);
                }
            }
        }

        this.showLandingPage();
    }

    setupStateSync() {
        // Set up two-way sync with state manager
        if (window.stateManager) {
            window.stateManager.addEventListener('sitemap:updated', (sitemap) => {
                this.currentSitemap = sitemap;
                this.updateJsonDisplay();
                this.updatePageCount();
            });

            window.stateManager.addEventListener('section:added', (data) => {
                this.renderSitemap(); // Re-render sitemap to show new section
            });

            window.stateManager.addEventListener('section:deleted', (data) => {
                this.renderSitemap(); // Re-render sitemap to remove section
            });

            window.stateManager.addEventListener('section:updated', (data) => {
                this.updateSectionInSitemap(data.pageId, data.sectionIndex, data.updates);
            });
        }
    }

    bindEvents() {
        // Generate sitemap
        document.getElementById('generateBtn').addEventListener('click', () => {
            const prompt = document.getElementById('promptInput').value.trim();
            if (prompt) {
                localStorage.setItem('initialPrompt', prompt);
                this.openBriefChat(prompt);
            } else {
                alert('Please enter a prompt');
            }
        });

        // Example prompts
        document.querySelectorAll('.example-tag').forEach(tag => {
            tag.addEventListener('click', (e) => {
                const prompt = e.target.dataset.prompt;
                localStorage.setItem('initialPrompt', prompt);
                document.getElementById('promptInput').value = prompt;
                this.openBriefChat(prompt);
            });
        });

        // Example link
        document.querySelector('.example-link').addEventListener('click', (e) => {
            const prompt = e.target.dataset.prompt;
            localStorage.setItem('initialPrompt', prompt);
            document.getElementById('promptInput').value = prompt;
            this.openBriefChat(prompt);
        });

        // Back button
        document.getElementById('backBtn').addEventListener('click', () => {
            this.showLandingPage();
        });

        // New project
        document.getElementById('newProjectBtn').addEventListener('click', () => {
            this.showLandingPage();
        });

        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Export JSON
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportJson();
        });

        // Share button
        document.getElementById('shareBtn').addEventListener('click', () => {
            // Mock share functionality
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {
                alert('Project link copied to clipboard!');
            }).catch(() => {
                alert('Share feature coming soon!');
            });
        });

        // Fit/Actual size toggle
        const fitToggleBtn = document.getElementById('fitToggleBtn');
        if (fitToggleBtn) {
            this.updateFitToggleLabel();
            fitToggleBtn.addEventListener('click', () => {
                this.autoFitSitemap = !this.autoFitSitemap;
                this.updateFitToggleLabel();
                if (this.lastSitemapContainer && this.lastSitemapDiv && this.lastSitemapWrapper) {
                    this.fitSitemapToViewport(this.lastSitemapContainer, this.lastSitemapDiv, this.lastSitemapWrapper);
                }
            });
        }

        // Generate wireframes
        document.getElementById('generateWireframeBtn').addEventListener('click', async () => {
            await this.openWireframePage();
        });

        // Copy JSON
        document.getElementById('copyJsonBtn').addEventListener('click', () => {
            this.copyJson();
        });

        // Enter key in prompt input
        document.getElementById('promptInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.ctrlKey || !this.isMobile()) {
                    const prompt = e.target.value.trim();
                    if (prompt) {
                        localStorage.setItem('initialPrompt', prompt);
                        this.openBriefChat(prompt);
                    }
                }
            }
        });

        // Auto-resize textarea
        document.getElementById('promptInput').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.max(44, e.target.scrollHeight) + 'px';
        });
    }

    showLandingPage() {
        document.getElementById('landingPage').style.display = 'block';
        document.getElementById('editorPage').style.display = 'none';

        // Reset state
        this.currentSitemap = null;
        document.getElementById('promptInput').value = '';
        this.disableControls();
    }

    openBriefChat(prompt = '') {
        const trimmedPrompt = typeof prompt === 'string' ? prompt.trim() : '';
        if (trimmedPrompt) {
            localStorage.setItem('initialPrompt', trimmedPrompt);
            window.location.href = `chat?prompt=${encodeURIComponent(trimmedPrompt)}`;
            return;
        }

        window.location.href = 'chat';
    }

    showEditorPage() {
        document.getElementById('landingPage').style.display = 'none';
        document.getElementById('editorPage').style.display = 'block';

        // Initialize with sitemap tab
        this.switchTab('sitemap');

        // Update displays
        this.updateJsonDisplay();
        this.updatePageCount();
    }

    switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        this.activeTab = tabName;

        if (tabName === 'wireframe') {
            if (this.currentSitemap) {
                // Store sitemap and navigate to wireframe page
                localStorage.setItem('currentSitemap', JSON.stringify(this.currentSitemap));
                window.location.href = 'wireframe.html';
            } else {
                alert('Please generate a sitemap first');
                // Switch back to sitemap tab visually
                this.switchTab('sitemap');
            }
            return;
        }

        // Ensure we show the sitemap/editor view
        const jsonTab = document.querySelector('.sidebar-tab:last-child');
        if (jsonTab) jsonTab.style.display = 'block';

        // Hide legacy wireframe tab content if it exists
        const wireframeTab = document.getElementById('wireframeTab');
        if (wireframeTab) wireframeTab.style.display = 'none';
    }

    async generateSitemap() {
        const prompt = document.getElementById('promptInput').value.trim();

        if (!prompt) {
            alert('Please enter a prompt to generate a sitemap');
            return;
        }

        this.showLoading(true);
        this.showEditorPage();
        this.updateStatus('Generating sitemap...');

        try {
            const response = await fetch(`${this.apiBaseUrl}/generate-sitemap/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (data.success) {
                this.currentSitemap = data.sitemap;
                document.getElementById('projectTitle').textContent = data.sitemap.website_type || 'Website Design Automation';
                this.renderSitemap();
                this.updateJsonDisplay();
                this.updatePageCount();
                this.enableControls();
                this.updateStatus('Ready');
            } else {
                alert('Error generating sitemap: ' + JSON.stringify(data.errors));
                this.updateStatus('Error');
                this.showLandingPage();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to generate sitemap. Please make sure the backend server is running on port 8000.');
            this.updateStatus('Connection error');
            this.showLandingPage();
        } finally {
            this.showLoading(false);
        }
    }

    renderSitemap() {
        console.log('🔄 Rendering hierarchical structure sitemap...');

        // Save state to localStorage for real-time sync with wireframe view
        if (this.currentSitemap) {
            localStorage.setItem('currentSitemap', JSON.stringify(this.currentSitemap));
        }

        const container = document.getElementById('sitemapContainer');
        container.innerHTML = '';

        if (!this.currentSitemap || !this.currentSitemap.pages) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No sitemap data available</h3>
                    <p>Please try generating the sitemap again</p>
                </div>
            `;
            return;
        }

        const sitemapDiv = document.createElement('div');
        sitemapDiv.className = 'sitemap-tree-hierarchical';

        // Find Home page and separate it from other pages
        const homePage = this.currentSitemap.pages.find(page =>
            page.name.toLowerCase() === 'home' || page.name.toLowerCase() === 'homepage'
        );
        const mainPages = this.currentSitemap.pages.filter(page =>
            page.name.toLowerCase() !== 'home' && page.name.toLowerCase() !== 'homepage'
        );

        console.log('🏠 Home page found:', homePage ? homePage.name : 'None');
        console.log('📄 Main pages:', mainPages.map(p => p.name));

        if (homePage) {
            // Step 1: Render Home page at top center
            this.renderHierarchicalHomeLevel(homePage, sitemapDiv);

            // Step 2: Render main pages if they exist
            if (mainPages.length > 0) {
                // Draw connectors from Home to main pages
                this.renderHierarchicalHomeToMainConnectors(sitemapDiv, mainPages.length);
                this.renderHierarchicalMainPagesLevel(mainPages, sitemapDiv);
            }
        } else {
            // Fallback: no Home page found
            this.renderHierarchicalMainPagesLevel(this.currentSitemap.pages, sitemapDiv);
            console.log('⚠️ No Home page found, using fallback layout');
        }

        const scaleWrapper = document.createElement('div');
        scaleWrapper.className = 'sitemap-scale-wrapper';
        scaleWrapper.appendChild(sitemapDiv);
        container.appendChild(scaleWrapper);

        this.lastSitemapContainer = container;
        this.lastSitemapDiv = sitemapDiv;
        this.lastSitemapWrapper = scaleWrapper;
        this.fitSitemapToViewport(container, sitemapDiv, scaleWrapper);

        // Add single global section selector panel (shared by all page cards)
        this.createGlobalSectionSelector(container);
    }

    fitSitemapToViewport(container, sitemapDiv, scaleWrapper) {
        if (!container || !sitemapDiv || !scaleWrapper) return;

        // Reset any previous scaling
        sitemapDiv.style.transform = 'translate(0px, 0px)';
        sitemapDiv.style.transformOrigin = 'top left';
        scaleWrapper.style.transform = 'scale(1)';
        scaleWrapper.style.transformOrigin = 'top left';
        scaleWrapper.style.width = '';
        scaleWrapper.style.height = '';

        // Measure after a tick to ensure layout is complete
        const applyFit = () => {
            const padding = 40;
            const availableWidth = Math.max(0, container.clientWidth - padding);
            const availableHeight = Math.max(0, container.clientHeight - padding);
            const cards = sitemapDiv.querySelectorAll('.page-card');
            let contentWidth = 0;
            let contentHeight = 0;
            let offsetX = 0;
            let offsetY = 0;

            if (cards.length) {
                const baseRect = sitemapDiv.getBoundingClientRect();
                let minLeft = Infinity;
                let minTop = Infinity;
                let maxRight = -Infinity;
                let maxBottom = -Infinity;

                cards.forEach(card => {
                    const r = card.getBoundingClientRect();
                    minLeft = Math.min(minLeft, r.left - baseRect.left);
                    minTop = Math.min(minTop, r.top - baseRect.top);
                    maxRight = Math.max(maxRight, r.right - baseRect.left);
                    maxBottom = Math.max(maxBottom, r.bottom - baseRect.top);
                });

                contentWidth = Math.max(1, maxRight - minLeft);
                contentHeight = Math.max(1, maxBottom - minTop);
                if (minLeft < 0) offsetX = -minLeft;
                if (minTop < 0) offsetY = -minTop;
            } else {
                const rect = sitemapDiv.getBoundingClientRect();
                contentWidth = rect.width || sitemapDiv.offsetWidth || 1;
                contentHeight = rect.height || sitemapDiv.offsetHeight || 1;
            }

            let scale = 1;
            if (this.autoFitSitemap) {
                const scaleX = availableWidth / contentWidth;
                const scaleY = availableHeight / contentHeight;
                scale = Math.min(1, scaleX, scaleY);
            }

            sitemapDiv.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
            scaleWrapper.style.transform = `scale(${scale})`;
            scaleWrapper.style.transformOrigin = 'top left';
            scaleWrapper.style.width = `${contentWidth * scale}px`;
            scaleWrapper.style.height = `${contentHeight * scale}px`;
            scaleWrapper.style.margin = '0 auto';
            if (this.autoFitSitemap) {
                container.scrollTop = 0;
                container.scrollLeft = 0;
            }
        };

        requestAnimationFrame(() => {
            applyFit();
            setTimeout(applyFit, 200);
        });
    }

    updateFitToggleLabel() {
        const btn = document.getElementById('fitToggleBtn');
        if (!btn) return;
        btn.textContent = this.autoFitSitemap ? 'Actual Size' : 'Fit to View';
    }

    renderHierarchicalHomeLevel(homePage, container) {
        const homeContainer = document.createElement('div');
        homeContainer.className = 'hierarchical-home-level';

        const homeCard = this.createPageCard(homePage, true, 0);
        homeContainer.appendChild(homeCard);

        container.appendChild(homeContainer);
    }

    renderHierarchicalHomeToMainConnectors(container, mainPageCount) {
        const connectorContainer = document.createElement('div');
        connectorContainer.className = 'hierarchical-home-to-main-connectors';

        // Step 1: Single vertical line down from Home (no arrowhead)
        const homeVerticalLine = document.createElement('div');
        homeVerticalLine.className = 'hierarchical-home-vertical-line';
        connectorContainer.appendChild(homeVerticalLine);

        // Step 2: Horizontal connector line (never touches cards)
        const horizontalConnector = document.createElement('div');
        horizontalConnector.className = 'hierarchical-main-horizontal-line';
        connectorContainer.appendChild(horizontalConnector);

        // Step 3: Individual vertical arrows down to each main page
        // We'll position these dynamically after the main pages are rendered
        // Store the connector container for later positioning
        connectorContainer.dataset.mainPageCount = mainPageCount;

        container.appendChild(connectorContainer);

        // Position connectors after a brief delay to allow layout to settle
        setTimeout(() => {
            this.positionMainPageConnectors(connectorContainer, mainPageCount);
        }, 10);
    }

    positionMainPageConnectors(connectorContainer, mainPageCount) {
        // Remove any existing connectors
        const existingConnectors = connectorContainer.querySelectorAll('.hierarchical-main-page-connector');
        existingConnectors.forEach(connector => connector.remove());

        // Find the main pages row to get actual positions
        const mainPagesRow = document.querySelector('.hierarchical-main-pages-row');
        if (!mainPagesRow) return;

        const pageContainers = mainPagesRow.querySelectorAll('.hierarchical-page-container');
        const connectorRect = connectorContainer.getBoundingClientRect();

        // Update horizontal line to span from first to last main page
        const horizontalLine = connectorContainer.querySelector('.hierarchical-main-horizontal-line');
        if (horizontalLine && pageContainers.length > 1) {
            const firstCard = pageContainers[0].querySelector('.page-card');
            const lastCard = pageContainers[pageContainers.length - 1].querySelector('.page-card');

            if (firstCard && lastCard) {
                const firstRect = firstCard.getBoundingClientRect();
                const lastRect = lastCard.getBoundingClientRect();

                const firstCenter = firstRect.left + (firstRect.width / 2);
                const lastCenter = lastRect.left + (lastRect.width / 2);

                const leftPercent = ((firstCenter - connectorRect.left) / connectorRect.width) * 100;
                const rightPercent = ((lastCenter - connectorRect.left) / connectorRect.width) * 100;

                horizontalLine.style.left = `${leftPercent}%`;
                horizontalLine.style.width = `${rightPercent - leftPercent}%`;
            }
        }

        pageContainers.forEach((pageContainer, index) => {
            const pageCard = pageContainer.querySelector('.page-card');
            if (!pageCard) return;

            const pageRect = pageCard.getBoundingClientRect();

            // Calculate the relative position of the page center
            const pageCenterX = pageRect.left + (pageRect.width / 2);
            const relativePosition = ((pageCenterX - connectorRect.left) / connectorRect.width) * 100;

            // Create connector arrow
            const mainPageArrow = document.createElement('div');
            mainPageArrow.className = 'hierarchical-main-page-connector';
            mainPageArrow.style.left = `${relativePosition}%`;
            connectorContainer.appendChild(mainPageArrow);
        });
    }

    renderHierarchicalMainPagesLevel(mainPages, container) {
        const mainPagesContainer = document.createElement('div');
        mainPagesContainer.className = 'hierarchical-main-pages-level';

        const mainPagesRow = document.createElement('div');
        mainPagesRow.className = 'hierarchical-main-pages-row';

        // Calculate required spacing based on subpages
        const pageSpacingInfo = this.calculatePageSpacing(mainPages);

        mainPages.forEach((page, index) => {
            // Create a container for each main page and its subpages
            const pageContainer = document.createElement('div');
            pageContainer.className = 'hierarchical-page-container';

            // Set dynamic width based on subpage requirements
            const requiredWidth = pageSpacingInfo[index];
            pageContainer.style.minWidth = `${requiredWidth}px`;
            pageContainer.style.flex = `0 0 ${requiredWidth}px`;

            // Add the main page card
            const pageCard = this.createPageCard(page, false, 1);
            pageContainer.appendChild(pageCard);

            // If this page has children, render them hierarchically below
            if (page.children && page.children.length > 0) {
                this.renderHierarchicalSubpages(pageContainer, page.children, index);
            }

            mainPagesRow.appendChild(pageContainer);
        });

        mainPagesContainer.appendChild(mainPagesRow);
        container.appendChild(mainPagesContainer);
    }

    calculatePageSpacing(mainPages) {
        const baseCardWidth = 280; // Width of each card
        const minGapBetweenCards = 30; // Minimum gap between cards
        const minPageContainerWidth = 320; // Minimum width for a page container

        return mainPages.map(page => {
            // Recursively calculate the maximum width needed for this page and all its descendants
            return this.calculateRequiredWidth(page, minPageContainerWidth);
        });
    }

    calculateRequiredWidth(page, minWidth) {
        if (!page.children || page.children.length === 0) {
            return minWidth;
        }

        const subpageCardWidth = 240; // Width of subpage cards
        const subpageGap = 30; // Gap between subpages
        const deepCardWidth = 220; // Width of deep nested cards
        const deepGap = 25; // Gap between deep nested cards

        // Calculate width needed for direct children
        let childrenTotalWidth = 0;

        page.children.forEach(child => {
            // Recursively get the width needed for each child and its descendants
            const childWidth = this.calculateRequiredWidth(child, subpageCardWidth);
            childrenTotalWidth += childWidth;
        });

        // Add gaps between children
        if (page.children.length > 1) {
            childrenTotalWidth += (page.children.length - 1) * subpageGap;
        }

        // Add padding
        const requiredWidth = Math.max(minWidth, childrenTotalWidth + 60);

        return requiredWidth;
    }

    renderHierarchicalSubpages(parentContainer, subpages, parentIndex) {
        // Create connector from parent to subpages
        const connectorContainer = document.createElement('div');
        connectorContainer.className = 'hierarchical-subpage-connectors';
        connectorContainer.dataset.subpageCount = subpages.length;

        // Step 1: Vertical line down from parent (no arrowhead here)
        const verticalLine = document.createElement('div');
        verticalLine.className = 'hierarchical-parent-vertical-line';
        connectorContainer.appendChild(verticalLine);

        if (subpages.length > 1) {
            // Step 2: Horizontal line connecting subpages (never touches cards)
            const horizontalLine = document.createElement('div');
            horizontalLine.className = 'hierarchical-subpage-horizontal-line';
            connectorContainer.appendChild(horizontalLine);

            // Connectors will be positioned dynamically after layout
        } else {
            // Single vertical connector with arrow for one subpage
            const singleConnector = document.createElement('div');
            singleConnector.className = 'hierarchical-single-subpage-connector';
            connectorContainer.appendChild(singleConnector);
        }

        parentContainer.appendChild(connectorContainer);

        // Create subpages row
        const subpagesRow = document.createElement('div');
        subpagesRow.className = 'hierarchical-subpages-row';

        subpages.forEach((subpage, index) => {
            // Create container for subpage and its children
            const subpageContainer = document.createElement('div');
            subpageContainer.className = 'hierarchical-subpage-container';

            // Calculate required width for this subpage based on its children
            const requiredWidth = this.calculateRequiredWidth(subpage, 240);
            subpageContainer.style.minWidth = `${requiredWidth}px`;
            subpageContainer.style.flex = `0 0 auto`;

            const subpageCard = this.createPageCard(subpage, false, 2);
            subpageContainer.appendChild(subpageCard);

            // If this subpage has children, render them below (Level 3+)
            if (subpage.children && subpage.children.length > 0) {
                this.renderDeepNestedPages(subpageContainer, subpage.children, 3);
            }

            subpagesRow.appendChild(subpageContainer);
        });

        parentContainer.appendChild(subpagesRow);

        // Position connectors dynamically after layout settles
        if (subpages.length > 1) {
            setTimeout(() => {
                this.positionSubpageConnectors(connectorContainer, subpagesRow);
            }, 10);
        }
    }

    positionSubpageConnectors(connectorContainer, subpagesRow) {
        // Remove any existing connectors
        const existingConnectors = connectorContainer.querySelectorAll('.hierarchical-subpage-connector');
        existingConnectors.forEach(connector => connector.remove());

        // Get the subpage containers
        const subpageContainers = subpagesRow.querySelectorAll('.hierarchical-subpage-container');
        if (subpageContainers.length === 0) return;

        const connectorRect = connectorContainer.getBoundingClientRect();
        const rowRect = subpagesRow.getBoundingClientRect();

        // Update horizontal line to span from first to last subpage
        const horizontalLine = connectorContainer.querySelector('.hierarchical-subpage-horizontal-line');
        if (horizontalLine && subpageContainers.length > 1) {
            const firstCard = subpageContainers[0].querySelector('.page-card');
            const lastCard = subpageContainers[subpageContainers.length - 1].querySelector('.page-card');

            if (firstCard && lastCard) {
                const firstRect = firstCard.getBoundingClientRect();
                const lastRect = lastCard.getBoundingClientRect();

                const firstCenter = firstRect.left + (firstRect.width / 2);
                const lastCenter = lastRect.left + (lastRect.width / 2);

                const leftPercent = ((firstCenter - connectorRect.left) / connectorRect.width) * 100;
                const rightPercent = ((lastCenter - connectorRect.left) / connectorRect.width) * 100;

                horizontalLine.style.left = `${leftPercent}%`;
                horizontalLine.style.width = `${rightPercent - leftPercent}%`;
            }
        }

        // Create connector arrows for each subpage
        subpageContainers.forEach((container, index) => {
            const pageCard = container.querySelector('.page-card');
            if (!pageCard) return;

            const cardRect = pageCard.getBoundingClientRect();
            const cardCenterX = cardRect.left + (cardRect.width / 2);
            const relativePosition = ((cardCenterX - connectorRect.left) / connectorRect.width) * 100;

            const connector = document.createElement('div');
            connector.className = 'hierarchical-subpage-connector';
            connector.style.left = `${relativePosition}%`;
            connectorContainer.appendChild(connector);
        });
    }

    renderDeepNestedPages(parentContainer, children, depth) {
        // Create connector from parent to children
        const connectorContainer = document.createElement('div');
        connectorContainer.className = 'hierarchical-deep-connectors';
        connectorContainer.dataset.childCount = children.length;

        // Vertical line down from parent
        const verticalLine = document.createElement('div');
        verticalLine.className = 'hierarchical-deep-vertical-line';
        connectorContainer.appendChild(verticalLine);

        if (children.length > 1) {
            // Horizontal line connecting children
            const horizontalLine = document.createElement('div');
            horizontalLine.className = 'hierarchical-deep-horizontal-line';
            connectorContainer.appendChild(horizontalLine);

            // Connectors will be positioned dynamically after layout
        } else {
            // Single vertical connector for one child
            const singleConnector = document.createElement('div');
            singleConnector.className = 'hierarchical-deep-single-connector';
            connectorContainer.appendChild(singleConnector);
        }

        parentContainer.appendChild(connectorContainer);

        // Create children row
        const childrenRow = document.createElement('div');
        childrenRow.className = 'hierarchical-deep-row';

        children.forEach((child, index) => {
            // Create container for child and its children (recursive)
            const childContainer = document.createElement('div');
            childContainer.className = 'hierarchical-deep-container';

            // Calculate required width for this child based on its descendants
            const requiredWidth = this.calculateRequiredWidth(child, 220);
            childContainer.style.minWidth = `${requiredWidth}px`;
            childContainer.style.flex = `0 0 auto`;

            const childCard = this.createPageCard(child, false, depth);
            childContainer.appendChild(childCard);

            // Recursively render deeper levels if this child has children
            if (child.children && child.children.length > 0) {
                this.renderDeepNestedPages(childContainer, child.children, depth + 1);
            }

            childrenRow.appendChild(childContainer);
        });

        parentContainer.appendChild(childrenRow);

        // Position connectors dynamically after layout settles
        if (children.length > 1) {
            setTimeout(() => {
                this.positionDeepConnectors(connectorContainer, childrenRow);
            }, 10);
        }
    }

    positionDeepConnectors(connectorContainer, childrenRow) {
        // Remove any existing connectors
        const existingConnectors = connectorContainer.querySelectorAll('.hierarchical-deep-connector');
        existingConnectors.forEach(connector => connector.remove());

        // Get the child containers
        const childContainers = childrenRow.querySelectorAll(':scope > .hierarchical-deep-container');
        if (childContainers.length === 0) return;

        const connectorRect = connectorContainer.getBoundingClientRect();

        // Update horizontal line to span from first to last child
        const horizontalLine = connectorContainer.querySelector('.hierarchical-deep-horizontal-line');
        if (horizontalLine && childContainers.length > 1) {
            const firstCard = childContainers[0].querySelector('.page-card');
            const lastCard = childContainers[childContainers.length - 1].querySelector('.page-card');

            if (firstCard && lastCard) {
                const firstRect = firstCard.getBoundingClientRect();
                const lastRect = lastCard.getBoundingClientRect();

                const firstCenter = firstRect.left + (firstRect.width / 2);
                const lastCenter = lastRect.left + (lastRect.width / 2);

                const leftPercent = ((firstCenter - connectorRect.left) / connectorRect.width) * 100;
                const rightPercent = ((lastCenter - connectorRect.left) / connectorRect.width) * 100;

                horizontalLine.style.left = `${leftPercent}%`;
                horizontalLine.style.width = `${rightPercent - leftPercent}%`;
            }
        }

        // Create connector arrows for each child
        childContainers.forEach((container, index) => {
            const pageCard = container.querySelector('.page-card');
            if (!pageCard) return;

            const cardRect = pageCard.getBoundingClientRect();
            const cardCenterX = cardRect.left + (cardRect.width / 2);
            const relativePosition = ((cardCenterX - connectorRect.left) / connectorRect.width) * 100;

            const connector = document.createElement('div');
            connector.className = 'hierarchical-deep-connector';
            connector.style.left = `${relativePosition}%`;
            connectorContainer.appendChild(connector);
        });
    }

    renderAllSubpageLevels(container, parentPages) {
        // Create a container for all subpage structures
        const subpagesContainer = document.createElement('div');
        subpagesContainer.className = 'all-subpages-container';

        // Create a single row for all subpages from all parents
        const allSubpagesRow = document.createElement('div');
        allSubpagesRow.className = 'all-subpages-row';
        allSubpagesRow.style.display = 'flex';
        allSubpagesRow.style.justifyContent = 'center';
        allSubpagesRow.style.alignItems = 'flex-start';
        allSubpagesRow.style.gap = '40px';
        allSubpagesRow.style.flexWrap = 'nowrap';
        allSubpagesRow.style.position = 'absolute';
        allSubpagesRow.style.top = '80px';
        allSubpagesRow.style.width = '100%';
        allSubpagesRow.style.left = '0';

        // Collect all subpages from all parents and render connectors
        let allSubpages = [];
        let subpageParentMap = new Map(); // Track which parent each subpage belongs to

        parentPages.forEach((parentPage, parentIndex) => {
            if (parentPage.children && parentPage.children.length > 0) {
                // Render connectors for this parent
                this.renderParentConnectors(subpagesContainer, parentPage, parentIndex, parentPages.length);

                // Add this parent's subpages to the collection
                parentPage.children.forEach(subpage => {
                    allSubpages.push(subpage);
                    subpageParentMap.set(subpage.id, parentIndex);
                });
            }
        });

        // Render all subpages in a single horizontal row
        allSubpages.forEach(subpage => {
            const subpageElement = this.createPageCard(subpage, false, 2);
            allSubpagesRow.appendChild(subpageElement);
        });

        subpagesContainer.appendChild(allSubpagesRow);

        // Set container height
        subpagesContainer.style.minHeight = '300px';

        container.appendChild(subpagesContainer);
    }

    renderParentConnectors(container, parentPage, parentIndex, totalParents) {
        // Create connector structure for this parent
        const connectorDiv = document.createElement('div');
        connectorDiv.className = `parent-${parentIndex}-connectors`;
        connectorDiv.style.position = 'absolute';
        connectorDiv.style.width = '100%';
        connectorDiv.style.height = '80px';
        connectorDiv.style.top = '0px';

        // Calculate parent position based on main pages layout
        const parentPosition = ((parentIndex + 0.5) / totalParents) * 100;

        // Vertical line down from this parent
        const verticalLine = document.createElement('div');
        verticalLine.className = 'parent-vertical-line';
        verticalLine.style.left = `${parentPosition}%`;
        connectorDiv.appendChild(verticalLine);

        // Calculate positions for this parent's subpages in the global subpage row
        const startIndex = this.getSubpageStartIndex(parentIndex, container);
        const subpageCount = parentPage.children.length;

        // Create connectors to each of this parent's subpages
        parentPage.children.forEach((subpage, subpageIndex) => {
            // Create individual connector from parent to each subpage
            const subpageConnector = document.createElement('div');
            subpageConnector.className = 'parent-to-subpage-connector';

            // Calculate the global position of this subpage in the row
            const globalSubpageIndex = startIndex + subpageIndex;
            const totalSubpages = this.getTotalSubpageCount(container);
            const subpagePosition = ((globalSubpageIndex + 0.5) / Math.max(totalSubpages, 1)) * 100;

            // Create a path from parent to subpage
            const connectorPath = document.createElement('div');
            connectorPath.className = 'connector-path';
            connectorPath.style.position = 'absolute';
            connectorPath.style.top = '40px';
            connectorPath.style.left = `${Math.min(parentPosition, subpagePosition)}%`;
            connectorPath.style.width = `${Math.abs(subpagePosition - parentPosition)}%`;
            connectorPath.style.height = '3px';
            connectorPath.style.background = '#374151';
            connectorPath.style.borderRadius = '1px';

            // Vertical line down to subpage
            const verticalToSubpage = document.createElement('div');
            verticalToSubpage.className = 'vertical-to-subpage';
            verticalToSubpage.style.position = 'absolute';
            verticalToSubpage.style.left = `${subpagePosition}%`;
            verticalToSubpage.style.top = '40px';
            verticalToSubpage.style.width = '3px';
            verticalToSubpage.style.height = '40px';
            verticalToSubpage.style.background = '#374151';
            verticalToSubpage.style.borderRadius = '1px';
            verticalToSubpage.style.transform = 'translateX(-50%)';

            // Add arrowhead
            const arrowhead = document.createElement('div');
            arrowhead.style.position = 'absolute';
            arrowhead.style.bottom = '-8px';
            arrowhead.style.left = '50%';
            arrowhead.style.transform = 'translateX(-50%)';
            arrowhead.style.width = '0';
            arrowhead.style.height = '0';
            arrowhead.style.borderLeft = '6px solid transparent';
            arrowhead.style.borderRight = '6px solid transparent';
            arrowhead.style.borderTop = '8px solid #374151';
            verticalToSubpage.appendChild(arrowhead);

            connectorDiv.appendChild(connectorPath);
            connectorDiv.appendChild(verticalToSubpage);
        });

        container.appendChild(connectorDiv);
    }

    getSubpageStartIndex(parentIndex, container) {
        // Calculate how many subpages come before this parent's subpages
        let startIndex = 0;
        const parentPages = this.getParentPagesWithSubpages();

        for (let i = 0; i < parentIndex; i++) {
            if (parentPages[i] && parentPages[i].children) {
                startIndex += parentPages[i].children.length;
            }
        }

        return startIndex;
    }

    getTotalSubpageCount(container) {
        // Count total subpages across all parents
        let totalCount = 0;
        const parentPages = this.getParentPagesWithSubpages();

        parentPages.forEach(parentPage => {
            if (parentPage.children) {
                totalCount += parentPage.children.length;
            }
        });

        return totalCount;
    }

    getParentPagesWithSubpages() {
        // Get all main pages that have subpages
        const mainPages = this.currentSitemap.pages.filter(page =>
            page.name.toLowerCase() !== 'home' && page.name.toLowerCase() !== 'homepage'
        );

        return mainPages.filter(page => page.children && page.children.length > 0);
    }

    renderLevel(pages, container, level, isRoot) {
        // Legacy method - kept for compatibility
        const levelContainer = document.createElement('div');
        levelContainer.className = `hierarchy-level level-${level}`;

        const pagesRow = document.createElement('div');
        pagesRow.className = 'pages-row';

        pages.forEach(page => {
            const pageElement = this.createPageCard(page, isRoot, level);
            pagesRow.appendChild(pageElement);
        });

        levelContainer.appendChild(pagesRow);
        container.appendChild(levelContainer);
    }

    createGlobalSectionSelector(container) {
        // Remove any existing global selector first
        const existingSelector = document.getElementById('globalSectionSelector');
        if (existingSelector) {
            existingSelector.remove();
        }

        const selectorHTML = `
            <div id="globalSectionSelector" class="section-selector-overlay" style="display: none;">
                <div class="section-selector-bar">
                    <div class="section-selector-header">
                        <h4>Add Section</h4>
                        <button class="close-selector-btn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    </div>
                    <div class="section-search">
                        <input type="text" class="section-search-input" placeholder="Search sections..." />
                    </div>
                    <div class="section-categories">
                        <div class="section-category">
                            <h5>Global Sections</h5>
                            <div class="section-options">
                                <div class="section-option" data-type="navbar" data-title="Navbar" data-description="Navigation bar with logo and main menu links">
                                    <div class="section-icon">🧭</div>
                                    <div class="section-info">
                                        <span class="section-name">Navbar</span>
                                        <span class="section-desc">Navigation menu</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="footer" data-title="Footer" data-description="Footer with contact info, social links, and secondary navigation">
                                    <div class="section-icon">📄</div>
                                    <div class="section-info">
                                        <span class="section-name">Footer</span>
                                        <span class="section-desc">Footer section</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                            </div>
                        </div>
                        <div class="section-category">
                            <h5>Page Types</h5>
                            <div class="section-options">
                                <div class="section-option" data-type="about" data-title="About Page" data-description="Company information, story, and team details">
                                    <div class="section-icon">ℹ️</div>
                                    <div class="section-info">
                                        <span class="section-name">About Page</span>
                                        <span class="section-desc">Company information</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="contact" data-title="Contact Page" data-description="Contact form, information, and location details">
                                    <div class="section-icon">📞</div>
                                    <div class="section-info">
                                        <span class="section-name">Contact Page</span>
                                        <span class="section-desc">Contact form and info</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="pricing" data-title="Pricing Page" data-description="Pricing plans, packages, and subscription options">
                                    <div class="section-icon">💰</div>
                                    <div class="section-info">
                                        <span class="section-name">Pricing Page</span>
                                        <span class="section-desc">Pricing and plans</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="blog" data-title="Blog Page" data-description="Blog posts, articles, and news content">
                                    <div class="section-icon">📝</div>
                                    <div class="section-info">
                                        <span class="section-name">Blog Page</span>
                                        <span class="section-desc">Blog and articles</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="gallery" data-title="Portfolio Page" data-description="Image gallery, portfolio, and project showcase">
                                    <div class="section-icon">🖼️</div>
                                    <div class="section-info">
                                        <span class="section-name">Portfolio Page</span>
                                        <span class="section-desc">Project showcase</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="features" data-title="Services Page" data-description="Services, features, and offerings overview">
                                    <div class="section-icon">⭐</div>
                                    <div class="section-info">
                                        <span class="section-name">Services Page</span>
                                        <span class="section-desc">Services overview</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                            </div>
                        </div>
                        <div class="section-category">
                            <h5>Content Sections</h5>
                            <div class="section-options">
                                <div class="section-option" data-type="hero" data-title="Hero Section" data-description="Hero section with compelling headline, subtext, and call-to-action">
                                    <div class="section-icon">🎯</div>
                                    <div class="section-info">
                                        <span class="section-name">Hero Section</span>
                                        <span class="section-desc">Main banner area</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="features" data-title="Features Section" data-description="Features grid showcasing key services or benefits">
                                    <div class="section-icon">⭐</div>
                                    <div class="section-info">
                                        <span class="section-name">Features</span>
                                        <span class="section-desc">Feature highlights</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="testimonial" data-title="Testimonial Section" data-description="Client testimonials and reviews">
                                    <div class="section-icon">💬</div>
                                    <div class="section-info">
                                        <span class="section-name">Testimonials</span>
                                        <span class="section-desc">Customer reviews</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="about" data-title="About Section" data-description="Company story, values, and background information">
                                    <div class="section-icon">ℹ️</div>
                                    <div class="section-info">
                                        <span class="section-name">About</span>
                                        <span class="section-desc">Company information</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="contact" data-title="Contact Section" data-description="Contact form and information">
                                    <div class="section-icon">📞</div>
                                    <div class="section-info">
                                        <span class="section-name">Contact</span>
                                        <span class="section-desc">Contact form</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="gallery" data-title="Gallery Section" data-description="Image gallery or portfolio showcase">
                                    <div class="section-icon">🖼️</div>
                                    <div class="section-info">
                                        <span class="section-name">Gallery</span>
                                        <span class="section-desc">Image showcase</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="pricing" data-title="Pricing Section" data-description="Pricing tables and package information">
                                    <div class="section-icon">💰</div>
                                    <div class="section-info">
                                        <span class="section-name">Pricing</span>
                                        <span class="section-desc">Pricing plans</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="blog" data-title="Blog Section" data-description="Blog posts and articles">
                                    <div class="section-icon">📝</div>
                                    <div class="section-info">
                                        <span class="section-name">Blog</span>
                                        <span class="section-desc">Blog content</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="stats" data-title="Stats Section" data-description="Statistics and key metrics">
                                    <div class="section-icon">📊</div>
                                    <div class="section-info">
                                        <span class="section-name">Stats</span>
                                        <span class="section-desc">Key statistics</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                                <div class="section-option" data-type="cta" data-title="Call to Action" data-description="Call-to-action section with buttons">
                                    <div class="section-icon">🎯</div>
                                    <div class="section-info">
                                        <span class="section-name">Call to Action</span>
                                        <span class="section-desc">Action buttons</span>
                                    </div>
                                    <button class="add-section-option-btn">+</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', selectorHTML);

        // Bind events to the global selector
        const globalSelector = document.getElementById('globalSectionSelector');
        const closeSelectorBtn = globalSelector.querySelector('.close-selector-btn');
        const sectionSearchInput = globalSelector.querySelector('.section-search-input');
        const addSectionOptionBtns = globalSelector.querySelectorAll('.add-section-option-btn');

        if (closeSelectorBtn) {
            closeSelectorBtn.addEventListener('click', () => {
                this.hideSectionSelector(globalSelector);
            });
        }

        if (sectionSearchInput) {
            sectionSearchInput.addEventListener('input', (e) => {
                this.filterSectionOptions(e.target.value, globalSelector);
            });
        }

        addSectionOptionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const option = btn.closest('.section-option');
                const sectionData = {
                    type: option.dataset.type,
                    title: option.dataset.title,
                    description: option.dataset.description
                };
                this.addSectionToPage(this.currentPageId, sectionData, this.currentInsertPosition, this.currentMode);
                this.hideSectionSelector(globalSelector);
            });
        });

        // Close on overlay click
        globalSelector.addEventListener('click', (e) => {
            if (e.target === globalSelector) {
                this.hideSectionSelector(globalSelector);
            }
        });
    }

    createPageCard(page, isRoot = false, depth = 0) {
        const card = document.createElement('div');
        card.className = `page-card ${isRoot ? 'root-page' : 'child-page'}`;
        card.dataset.pageId = page.id;
        card.dataset.depth = depth;

        // Create sections based on page type and PERSIST them to page data
        const sections = this.generatePageSections(page);

        // IMPORTANT: Save generated sections to page data for synchronization
        if (!page.sections || page.sections.length === 0) {
            page.sections = sections;
            // Update localStorage to persist sections
            if (this.currentSitemap) {
                localStorage.setItem('currentSitemap', JSON.stringify(this.currentSitemap));
            }
        }

        // Add hierarchy indicator
        const hierarchyIndicator = depth > 0 ? `
            <div class="hierarchy-indicator">
                <span class="depth-badge">Level ${depth}</span>
            </div>
        ` : '';

        card.innerHTML = `
            ${hierarchyIndicator}
            <!-- Delete button - always visible at top right corner -->
            <button class="page-delete-btn" title="Delete page">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
            
            <!-- Add child page button - visible at bottom center -->
            <button class="add-child-page-btn" title="Add child page">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
            </button>
            
            <div class="page-header">
                <div class="page-title-section">
                    <div class="page-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"/>
                            <path d="M8 21v-4a2 2 0 012-2h2a2 2 0 012 2v4"/>
                        </svg>
                    </div>
                    <input type="text" class="page-name" value="${page.name}" />
                </div>
                <div class="page-actions">
                    <button class="page-menu-btn" title="Page options">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="1"/>
                            <circle cx="19" cy="12" r="1"/>
                            <circle cx="5" cy="12" r="1"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="page-content">
                ${sections.map((section, index) => {
            const title = section.title || 'New Section';
            const description = section.description || (section.content || ''); // Fallback to content if description is missing
            return `
                    <div class="section-wrapper" data-section-index="${index}">
                        <button class="section-regenerate-btn" title="Regenerate description">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M23 4v6h-6"/>
                                <path d="M1 20v-6h6"/>
                                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                            </svg>
                        </button>
                        <button class="section-delete-btn" title="Delete section">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                        <div class="page-section" data-section-type="${section.type}" data-section-index="${index}">
                            <div class="section-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                    <line x1="9" y1="9" x2="15" y2="9"/>
                                    <line x1="9" y1="12" x2="15" y2="12"/>
                                    <line x1="9" y1="15" x2="15" y2="15"/>
                                </svg>
                            </div>
                            <div class="section-content">
                                <div class="section-header">
                                    <input type="text" class="section-title-input" value="${title}" />
                                </div>
                                <div class="section-description">
                                    <textarea class="section-description-input" placeholder="Enter section description...">${description}</textarea>
                                </div>
                            </div>
                        </div>
                        <!-- Plus button appears here when section is selected -->
                        <div class="section-plus-button" style="display: none;">
                            <button class="add-section-between-btn" data-insert-after="${index}">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="12" y1="5" x2="12" y2="19"/>
                                    <line x1="5" y1="12" x2="19" y2="12"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                `;
        }).join('')}
                
                <!-- Add section at the end -->
                <div class="add-section-end">
                    <button class="add-section-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        Add Section
                    </button>
                </div>
                
                <!-- Generate Content Button -->
                <button class="generate-content-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                    Generate content
                </button>
            </div>
        `;

        // Bind events AFTER innerHTML is set
        const deleteBtn = card.querySelector('.page-delete-btn');
        const addChildBtn = card.querySelector('.add-child-page-btn');
        const pageName = card.querySelector('.page-name');
        const addSectionBtn = card.querySelector('.add-section-btn');
        const generateContentBtn = card.querySelector('.generate-content-btn');

        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deletePage(page.id);
            });
        }

        if (addChildBtn) {
            addChildBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addChildPage(page.id);
            });
        }

        if (pageName) {
            pageName.addEventListener('blur', () => this.updatePageName(page.id, pageName.value));
            pageName.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    pageName.blur();
                }
            });
        }


        if (addSectionBtn) {
            addSectionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const globalSelector = document.getElementById('globalSectionSelector');
                this.showSectionSelector(page.id, globalSelector, -1); // -1 means add at end
            });
        }

        if (generateContentBtn) {
            generateContentBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.generateContent(page.id);
            });
        }

        // Bind section click events (Relume-style)
        card.querySelectorAll('.page-section').forEach((sectionEl, index) => {
            sectionEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectSection(page.id, index, card);
            });
        });

        // Bind section delete buttons
        card.querySelectorAll('.section-delete-btn').forEach((btn, index) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSection(page.id, index);
            });
        });

        // Bind section regenerate buttons
        card.querySelectorAll('.section-regenerate-btn').forEach((btn, index) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.regenerateSection(page.id, index, btn);
            });
        });

        // Bind section title inputs
        card.querySelectorAll('.section-title-input').forEach((input, index) => {
            input.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent section selection when editing
            });
            input.addEventListener('blur', () => {
                this.updateSectionTitle(page.id, index, input.value);
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    input.blur();
                }
            });
        });

        // Bind section description inputs
        card.querySelectorAll('.section-description-input').forEach((textarea, index) => {
            textarea.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent section selection when editing
            });
            textarea.addEventListener('blur', () => {
                this.updateSectionDescription(page.id, index, textarea.value);
            });
            // Auto-resize textarea
            textarea.addEventListener('input', () => {
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            });
        });

        // Bind plus buttons between sections
        card.querySelectorAll('.add-section-between-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const insertAfter = parseInt(btn.dataset.insertAfter);
                const globalSelector = document.getElementById('globalSectionSelector');
                this.showSectionSelector(page.id, globalSelector, insertAfter);
            });
        });



        // Click outside to deselect sections
        document.addEventListener('click', (e) => {
            if (!card.contains(e.target)) {
                this.deselectAllSections(card);
            }
        });

        return card;
    }

    generatePageSections(page) {
        if (page.sections && page.sections.length > 0) {
            return page.sections;
        }
        return [];
    }

    addSection(pageId) {
        // This method is now replaced by showSectionSelector
        console.log('Use showSectionSelector instead');
    }

    selectSection(pageId, sectionIndex, pageCard) {
        // Deselect all sections first
        this.deselectAllSections(pageCard);

        // Select the clicked section
        const sectionWrapper = pageCard.querySelector(`[data-section-index="${sectionIndex}"]`);
        if (sectionWrapper) {
            sectionWrapper.classList.add('selected');

            // Show the plus button after this section
            const plusButton = sectionWrapper.querySelector('.section-plus-button');
            if (plusButton) {
                plusButton.style.display = 'flex';
            }
        }
    }

    deselectAllSections(pageCard) {
        // Remove selection from all sections
        pageCard.querySelectorAll('.section-wrapper').forEach(wrapper => {
            wrapper.classList.remove('selected');
            const plusButton = wrapper.querySelector('.section-plus-button');
            if (plusButton) {
                plusButton.style.display = 'none';
            }
        });
    }

    showSectionSelector(pageId, selectorElement, insertPosition = -1, mode = 'section') {
        this.currentInsertPosition = insertPosition;
        this.currentPageId = pageId;
        this.currentMode = mode; // 'section' or 'child-page'

        // Hide all other section selectors first
        document.querySelectorAll('.section-selector-overlay').forEach(overlay => {
            if (overlay !== selectorElement) {
                overlay.style.display = 'none';
            }
        });

        // Update header text based on mode
        const header = selectorElement.querySelector('.section-selector-header h4');
        if (header) {
            header.textContent = mode === 'child-page' ? 'Add Child Page' : 'Add Section';
        }

        // Update instance counts for all section types
        this.updateSectionInstanceCounts(selectorElement);

        // Show the section selector overlay
        selectorElement.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling

        // Focus on search input
        const searchInput = selectorElement.querySelector('.section-search-input');
        if (searchInput) {
            setTimeout(() => searchInput.focus(), 100);
        }
    }

    updateSectionInstanceCounts(selectorElement) {
        // Count instances of each section type across all pages
        const instanceCounts = this.countSectionInstances();

        // Update each section option with its instance count
        const sectionOptions = selectorElement.querySelectorAll('.section-option');
        sectionOptions.forEach(option => {
            const sectionType = option.dataset.type;
            const count = instanceCounts[sectionType] || 0;

            // Find or create the instance count element
            let instanceCount = option.querySelector('.section-instance-count');
            if (!instanceCount) {
                instanceCount = document.createElement('span');
                instanceCount.className = 'section-instance-count';
                // Insert after section-desc
                const sectionInfo = option.querySelector('.section-info');
                if (sectionInfo) {
                    sectionInfo.appendChild(instanceCount);
                }
            }

            // Update the count text
            if (count > 0) {
                instanceCount.textContent = `${count} instance${count !== 1 ? 's' : ''}`;
                instanceCount.style.display = 'block';
            } else {
                instanceCount.style.display = 'none';
            }
        });
    }

    countSectionInstances() {
        const counts = {};

        // Recursively count sections in all pages
        const countInPages = (pages) => {
            if (!pages) return;

            pages.forEach(page => {
                if (page.sections) {
                    page.sections.forEach(section => {
                        const type = section.type;
                        counts[type] = (counts[type] || 0) + 1;
                    });
                }

                // Recursively count in child pages
                if (page.children && page.children.length > 0) {
                    countInPages(page.children);
                }
            });
        };

        if (this.currentSitemap && this.currentSitemap.pages) {
            countInPages(this.currentSitemap.pages);
        }

        return counts;
    }

    addChildPage(parentId) {
        console.log('➕ Adding child page to parent:', parentId);

        const newPage = {
            id: this.generateId(),
            name: 'New Page',
            description: 'Page description',
            children: []
        };

        // Find the parent page to determine where to add
        const parentPage = this.findPageById(parentId);

        if (!parentPage) {
            console.log('❌ Parent page not found:', parentId);
            return;
        }

        // Check if parent is the Home page (root level)
        const isHomePage = parentPage.name.toLowerCase() === 'home' || parentPage.name.toLowerCase() === 'homepage';

        if (isHomePage) {
            // For Home page, add as a new main page (sibling to other main pages)
            console.log('🏠 Adding new main page (Home is parent)');
            this.currentSitemap.pages.push(newPage);
        } else {
            // For other pages, add as a child
            console.log('📄 Adding as child page');
            if (!parentPage.children) {
                parentPage.children = [];
            }
            parentPage.children.push(newPage);
        }

        console.log('✅ Page added successfully');
        this.renderSitemap();
        this.updateJsonDisplay();
        this.updatePageCount();
    }

    addChildPageFromSection(parentId, sectionData) {
        // Create page name based on section type
        const pageNames = {
            'navbar': 'Navigation',
            'footer': 'Footer',
            'hero': 'Landing Page',
            'features': 'Features',
            'testimonial': 'Testimonials',
            'about': 'About Us',
            'contact': 'Contact',
            'gallery': 'Gallery',
            'pricing': 'Pricing',
            'blog': 'Blog',
            'stats': 'Statistics',
            'cta': 'Get Started'
        };

        const newPage = {
            id: this.generateId(),
            name: pageNames[sectionData.type] || sectionData.title,
            description: sectionData.description,
            children: [],
            sections: [sectionData] // Initialize with the selected section
        };

        this.addPageToSitemap(parentId, newPage);
        this.renderSitemap();
        this.updateJsonDisplay();
        this.updatePageCount();
    }

    addSectionToPage(pageId, sectionData, insertPosition = -1) {
        const page = this.findPageById(pageId);
        if (page) {
            // Initialize sections array if it doesn't exist
            if (!page.sections) {
                page.sections = this.generatePageSections(page);
            }

            // Insert section at the specified position
            if (insertPosition === -1) {
                // Add at the end
                page.sections.push(sectionData);
            } else {
                // Insert after the specified index
                page.sections.splice(insertPosition + 1, 0, sectionData);
            }

            // Re-render the sitemap to show the new section
            this.renderSitemap();
            this.updateJsonDisplay();
        }
    }

    hideSectionSelector(selectorElement) {
        selectorElement.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling

        // Reset mode and tracking variables
        this.currentMode = 'section';
        this.currentPageId = null;
        this.currentInsertPosition = -1;

        // Clear search
        const searchInput = selectorElement.querySelector('.section-search-input');
        if (searchInput) {
            searchInput.value = '';
            const pageCard = selectorElement.closest('.page-card');
            if (pageCard) {
                this.filterSectionOptions('', pageCard);
            }
        }

        // Reset header text
        const header = selectorElement.querySelector('.section-selector-header h4');
        if (header) {
            header.textContent = 'Add Section';
        }
    }

    filterSectionOptions(searchTerm, container) {
        if (!container || !container.querySelectorAll) return;
        const options = container.querySelectorAll('.section-option');
        if (!options || options.length === 0) return;
        const lowerSearchTerm = searchTerm.toLowerCase();

        options.forEach(option => {
            const name = option.querySelector('.section-name').textContent.toLowerCase();
            const desc = option.querySelector('.section-desc').textContent.toLowerCase();

            if (name.includes(lowerSearchTerm) || desc.includes(lowerSearchTerm)) {
                option.style.display = 'flex';
            } else {
                option.style.display = 'none';
            }
        });
    }

    deleteSection(pageId, sectionIndex) {
        const page = this.findPageById(pageId);
        if (page) {
            // Ensure page sections exist
            if (!page.sections) {
                page.sections = this.generatePageSections(page);
            }

            if (page.sections[sectionIndex]) {
                page.sections.splice(sectionIndex, 1);
                this.renderSitemap();
                this.updateJsonDisplay();
            }
        }
    }

    updateSectionTitle(pageId, sectionIndex, newTitle) {
        const page = this.findPageById(pageId);
        if (page) {
            // Ensure page sections exist
            if (!page.sections) {
                page.sections = this.generatePageSections(page);
            }

            if (page.sections[sectionIndex]) {
                page.sections[sectionIndex].title = newTitle;
                this.updateJsonDisplay();
            }
        }
    }

    updateSectionDescription(pageId, sectionIndex, newDescription) {
        const page = this.findPageById(pageId);
        if (page) {
            // Ensure page sections exist
            if (!page.sections) {
                page.sections = this.generatePageSections(page);
            }

            if (page.sections[sectionIndex]) {
                page.sections[sectionIndex].description = newDescription;
                this.updateJsonDisplay();
            }
        }
    }

    async regenerateSection(pageId, sectionIndex, button) {
        const page = this.findPageById(pageId);
        if (!page || !page.sections || !page.sections[sectionIndex]) return;

        const section = page.sections[sectionIndex];
        const icon = button.querySelector('svg');

        // Add rotation animation
        icon.style.transition = 'transform 0.5s ease-in-out';
        icon.style.transform = 'rotate(360deg)';
        button.disabled = true;
        button.style.opacity = '0.7';

        try {
            const response = await fetch(`${this.apiBaseUrl}/regenerate-section/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: section.title,
                    type: section.type
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update sitemap data
                section.description = data.description;

                // Update UI directly
                const pageCard = document.querySelector(`.page-card[data-page-id="${pageId}"]`);
                if (pageCard) {
                    const textarea = pageCard.querySelectorAll('.section-description-input')[sectionIndex];
                    if (textarea) {
                        textarea.value = data.description;
                        // Trigger auto-resize
                        textarea.style.height = 'auto';
                        textarea.style.height = textarea.scrollHeight + 'px';

                        // Brief pulse effect to show change
                        textarea.style.backgroundColor = 'rgba(99, 102, 241, 0.05)';
                        setTimeout(() => {
                            textarea.style.backgroundColor = 'transparent';
                        }, 1000);
                    }
                }

                this.updateJsonDisplay();
                this.updateStatus('Section description regenerated');
            } else {
                alert('Failed to regenerate section');
            }
        } catch (error) {
            console.error('Regeneration error:', error);
            alert('Failed to connect to regeneration service');
        } finally {
            // Reset button state
            setTimeout(() => {
                icon.style.transform = 'rotate(0deg)';
                button.disabled = false;
                button.style.opacity = '1';
                icon.style.transition = 'none';
            }, 500);
        }
    }

    generateContent(pageId) {
        // Generate content for the page using AI
        const page = this.findPageById(pageId);
        if (page) {
            alert(`Generating AI content for ${page.name}. This feature will be fully implemented in the next update.`);
            console.log('Generating content for page:', pageId);
        }
    }

    findPageById(pageId) {
        const findInPages = (pages) => {
            for (let page of pages) {
                if (page.id === pageId) {
                    return page;
                }
                if (page.children) {
                    const found = findInPages(page.children);
                    if (found) return found;
                }
            }
            return null;
        };

        return findInPages(this.currentSitemap.pages);
    }

    addRootPage() {
        const newPage = {
            id: this.generateId(),
            name: 'New Page',
            description: 'Page description',
            children: []
        };

        if (!this.currentSitemap.pages) {
            this.currentSitemap.pages = [];
        }

        this.currentSitemap.pages.push(newPage);
        this.renderSitemap();
        this.updateJsonDisplay();
        this.updatePageCount();
    }

    deletePage(pageId) {
        if (confirm('Are you sure you want to delete this page and all its children?')) {
            this.removePageFromSitemap(pageId);
            this.renderSitemap();
            this.updateJsonDisplay();
            this.updatePageCount();
        }
    }

    updatePageName(pageId, newName) {
        this.updatePageInSitemap(pageId, { name: newName });
        this.updateJsonDisplay();
    }

    addPageToSitemap(parentId, newPage) {
        const addToPages = (pages) => {
            for (let page of pages) {
                if (page.id === parentId) {
                    if (!page.children) page.children = [];
                    page.children.push(newPage);
                    return true;
                }
                if (page.children && addToPages(page.children)) {
                    return true;
                }
            }
            return false;
        };

        return addToPages(this.currentSitemap.pages);
    }

    removePageFromSitemap(pageId) {
        const removeFromPages = (pages) => {
            for (let i = 0; i < pages.length; i++) {
                if (pages[i].id === pageId) {
                    pages.splice(i, 1);
                    return true;
                }
                if (pages[i].children && removeFromPages(pages[i].children)) {
                    return true;
                }
            }
            return false;
        };

        removeFromPages(this.currentSitemap.pages);
    }

    updatePageInSitemap(pageId, updates) {
        const updateInPages = (pages) => {
            for (let page of pages) {
                if (page.id === pageId) {
                    Object.assign(page, updates);
                    return true;
                }
                if (page.children && updateInPages(page.children)) {
                    return true;
                }
            }
            return false;
        };

        updateInPages(this.currentSitemap.pages);
    }

    updateJsonDisplay() {
        const jsonOutput = document.getElementById('jsonOutput');
        const displayData = this.currentSitemap || {
            website_type: "",
            pages: []
        };
        jsonOutput.textContent = JSON.stringify(displayData, null, 2);
    }

    updatePageCount() {
        const count = this.countPages();
        document.getElementById('pageCount').textContent = `${count} page${count !== 1 ? 's' : ''}`;
    }

    countPages() {
        if (!this.currentSitemap || !this.currentSitemap.pages) return 0;

        const countInPages = (pages) => {
            let count = pages.length;
            pages.forEach(page => {
                if (page.children) {
                    count += countInPages(page.children);
                }
            });
            return count;
        };

        return countInPages(this.currentSitemap.pages);
    }

    updateStatus(message) {
        document.querySelector('.status-text').textContent = message;
    }

    async exportJson() {
        if (!this.currentSitemap) {
            alert('No sitemap data to export');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/export-json/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sitemap_data: this.currentSitemap })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sitemap.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.updateStatus('Exported successfully');
            } else {
                alert('Failed to export JSON');
            }
        } catch (error) {
            console.error('Export error:', error);
            alert('Failed to export JSON');
        }
    }

    async openWireframePage() {
        if (!this.currentSitemap) {
            alert('Please generate a sitemap first');
            return;
        }

        this.showLoading(true);
        this.updateStatus('Generating AI wireframes from sitemap...');

        try {
            const response = await fetch(`${this.apiBaseUrl}/generate-wireframe/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sitemap_data: this.currentSitemap })
            });

            const data = await response.json();

            if (!data.success || !data.wireframes || !data.wireframes.wireframes) {
                throw new Error(data.error || 'Wireframe generation failed');
            }

            const wireframesMap = data.wireframes.wireframes;
            const attachSections = (pages) => {
                if (!Array.isArray(pages)) return;

                pages.forEach(page => {
                    if (wireframesMap[page.id] && Array.isArray(wireframesMap[page.id].sections)) {
                        page.sections = wireframesMap[page.id].sections;
                    }

                    if (page.children && page.children.length > 0) {
                        attachSections(page.children);
                    }
                });
            };

            attachSections(this.currentSitemap.pages);

            localStorage.setItem('currentSitemap', JSON.stringify(this.currentSitemap));
            this.updateJsonDisplay();
            this.updateStatus('Wireframes ready');
            window.location.href = 'wireframe.html';
        } catch (error) {
            console.error('Wireframe generation error:', error);
            alert('Failed to generate AI wireframes from the current sitemap.');
            this.updateStatus('Connection error');
        } finally {
            this.showLoading(false);
        }
    }

    async generateWireframes() {
        if (!this.currentSitemap) {
            alert('No sitemap data available for wireframe generation');
            return;
        }

        this.showLoading(true);
        this.updateStatus('Generating wireframes...');

        try {
            const response = await fetch(`${this.apiBaseUrl}/generate-wireframe/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sitemap_data: this.currentSitemap })
            });

            const data = await response.json();

            if (data.success) {
                this.displayWireframes(data.wireframes);
                this.updateStatus('Wireframes generated');
            } else {
                alert('Error generating wireframes: ' + data.error);
                this.updateStatus('Error');
            }
        } catch (error) {
            console.error('Wireframe error:', error);
            alert('Failed to generate wireframes');
            this.updateStatus('Connection error');
        } finally {
            this.showLoading(false);
        }
    }

    displayWireframes(wireframes) {
        const content = document.getElementById('wireframeContent');
        content.innerHTML = '';

        // Create wireframe tree structure
        const wireframeTree = document.createElement('div');
        wireframeTree.className = 'wireframe-tree';

        // Render wireframes in hierarchical structure
        this.renderWireframeTree(this.currentSitemap.pages, wireframes.wireframes, wireframeTree);

        content.appendChild(wireframeTree);
    }

    renderWireframeTree(pages, wireframeData, container, level = 0) {
        pages.forEach((page, index) => {
            const wireframe = wireframeData[page.id];
            if (!wireframe) return;

            // Create wireframe card
            const wireframeCard = document.createElement('div');
            wireframeCard.className = `wireframe-card ${level === 0 ? 'root-wireframe' : 'child-wireframe'}`;
            wireframeCard.style.marginLeft = `${level * 20}px`;
            wireframeCard.dataset.level = level;

            // Add connection line for child pages
            if (level > 0) {
                wireframeCard.classList.add('has-connection');
            }

            // Add hierarchy badge
            const hierarchyBadge = level > 0 ? `
                <div class="wireframe-hierarchy-badge">
                    <span class="level-indicator">L${level}</span>
                </div>
            ` : '';

            wireframeCard.innerHTML = `
                ${hierarchyBadge}
                <div class="wireframe-header">
                    <div class="wireframe-icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                            <line x1="9" y1="9" x2="15" y2="9"/>
                            <line x1="9" y1="12" x2="15" y2="12"/>
                            <line x1="9" y1="15" x2="15" y2="15"/>
                        </svg>
                    </div>
                    <h4 class="wireframe-title">${wireframe.page_name}</h4>
                    <div class="wireframe-path">${wireframe.page_path}</div>
                    <button class="wireframe-expand-btn" title="View details">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6,9 12,15 18,9"/>
                        </svg>
                    </button>
                </div>
                <div class="wireframe-sections" style="display: none;">
                    <div class="wf-container">
                        ${wireframe.sections.map(section => this.renderRelumeSection(section)).join('')}
                    </div>
                </div>
            `;

            // Add expand/collapse functionality
            const expandBtn = wireframeCard.querySelector('.wireframe-expand-btn');
            const sectionsDiv = wireframeCard.querySelector('.wireframe-sections');

            expandBtn.addEventListener('click', () => {
                const isExpanded = sectionsDiv.style.display !== 'none';
                sectionsDiv.style.display = isExpanded ? 'none' : 'block';
                expandBtn.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
            });

            container.appendChild(wireframeCard);

            // Render children recursively
            if (page.children && page.children.length > 0) {
                this.renderWireframeTree(page.children, wireframeData, container, level + 1);
            }
        });
    }

    renderRelumeSection(section) {
        const type = section.type.toLowerCase();

        if (type === 'navbar') {
            return `
                <div class="wf-navbar">
                    <div class="wf-logo">LOGO</div>
                    <div class="wf-nav-links">
                        <div class="wf-link">Home</div>
                        <div class="wf-link">About</div>
                        <div class="wf-link">Services</div>
                        <div class="wf-link">Contact</div>
                    </div>
                    <div class="wf-btn" style="padding: 8px 16px; font-size: 14px;">Button</div>
                </div>
            `;
        } else if (type === 'hero') {
            return `
                <div class="wf-section">
                    <div class="wf-hero">
                        <div class="wf-hero-content">
                            <div class="wf-h1">${section.title || 'Hero Headline'}</div>
                            <div class="wf-p">${section.description || 'Subheadline goes here. Explain the value proposition clearly.'}</div>
                            <div class="wf-btn">Button</div>
                        </div>
                        <div class="wf-image-placeholder"></div>
                    </div>
                </div>
            `;
        } else if (type === 'features' || type === 'services' || type === 'products') {
            return `
                <div class="wf-section">
                    <div class="wf-hero-content" style="text-align: center; align-items: center; margin-bottom: 40px;">
                        <h2 style="font-size: 36px; font-weight: 800;">${section.title || 'Features'}</h2>
                        <p class="wf-p" style="max-width: 600px;">${section.description || 'Description of the features section.'}</p>
                    </div>
                    <div class="wf-grid-3">
                        <div class="wf-card">
                            <div class="wf-icon"></div>
                            <h3 style="font-weight: 700; font-size: 20px;">Feature One</h3>
                            <p class="wf-p">Description of the feature.</p>
                        </div>
                        <div class="wf-card">
                            <div class="wf-icon"></div>
                            <h3 style="font-weight: 700; font-size: 20px;">Feature Two</h3>
                            <p class="wf-p">Description of the feature.</p>
                        </div>
                        <div class="wf-card">
                            <div class="wf-icon"></div>
                            <h3 style="font-weight: 700; font-size: 20px;">Feature Three</h3>
                            <p class="wf-p">Description of the feature.</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (type === 'footer') {
            return `
                <div class="wf-footer">
                    <div class="wf-footer-col">
                        <div class="wf-logo" style="background: #fff; color: #000; margin-bottom: 20px;">LOGO</div>
                        <p style="color: #999; font-size: 14px;">Address and contact info.</p>
                    </div>
                    <div class="wf-footer-col">
                        <h4 style="font-weight: 700; margin-bottom: 16px;">Column One</h4>
                        <a href="#" class="wf-footer-link">Link One</a>
                        <a href="#" class="wf-footer-link">Link Two</a>
                        <a href="#" class="wf-footer-link">Link Three</a>
                    </div>
                    <div class="wf-footer-col">
                        <h4 style="font-weight: 700; margin-bottom: 16px;">Column Two</h4>
                        <a href="#" class="wf-footer-link">Link One</a>
                        <a href="#" class="wf-footer-link">Link Two</a>
                        <a href="#" class="wf-footer-link">Link Three</a>
                    </div>
                    <div class="wf-footer-col">
                        <h4 style="font-weight: 700; margin-bottom: 16px;">Column Three</h4>
                        <a href="#" class="wf-footer-link">Link One</a>
                        <a href="#" class="wf-footer-link">Link Two</a>
                        <a href="#" class="wf-footer-link">Link Three</a>
                    </div>
                </div>
            `;
        } else {
            // Generic section
            return `
                <div class="wf-section">
                    <div class="wf-hero-content">
                        <h2 style="font-size: 32px; font-weight: 800;">${section.title || 'Section Title'}</h2>
                        <p class="wf-p">${section.description || 'Section description text.'}</p>
                    </div>
                </div>
            `;
        }
    }

    exportJson() {
        if (!this.currentSitemap) return;

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.currentSitemap, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "sitemap.json");
        document.body.appendChild(downloadAnchorNode); // required for firefox
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    }

    copyJson() {
        const jsonOutput = document.getElementById('jsonOutput');
        navigator.clipboard.writeText(jsonOutput.textContent).then(() => {
            const btn = document.getElementById('copyJsonBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                </svg>
                Copied
            `;
            setTimeout(() => {
                btn.innerHTML = originalText;
            }, 2000);
        }).catch(() => {
            alert('Failed to copy JSON to clipboard');
        });
    }

    enableControls() {
        document.getElementById('exportBtn').disabled = false;
        document.getElementById('generateWireframeBtn').disabled = false;
        document.getElementById('copyJsonBtn').disabled = false;
    }

    disableControls() {
        document.getElementById('exportBtn').disabled = true;
        document.getElementById('generateWireframeBtn').disabled = true;
        document.getElementById('copyJsonBtn').disabled = true;
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    generateId() {
        return Math.random().toString(36).substring(2, 10);
    }

    isMobile() {
        return window.innerWidth <= 768;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SitemapApp();
});

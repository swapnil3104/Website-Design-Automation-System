class WireframeApp {
    constructor() {
        this.selectedPageForExport = null;
        this.init();
    }

    init() {
        this.bindEvents();
        // Load sitemap data if available
        this.loadSitemap();
    }

    loadSitemap() {
        const savedSitemap = localStorage.getItem('currentSitemap');
        if (savedSitemap && window.stateManager) {
            try {
                const sitemap = JSON.parse(savedSitemap);
                console.log("📱 Loading sitemap from localStorage (BEFORE dedup):", sitemap);
                console.log("📊 Original page count:", sitemap.pages ? sitemap.pages.length : 0);

                // CRITICAL FIX: Deduplicate pages by ID
                if (sitemap.pages && Array.isArray(sitemap.pages)) {
                    const seenIds = new Set();
                    const uniquePages = [];
                    const duplicates = [];

                    sitemap.pages.forEach((page, index) => {
                        if (page.id && !seenIds.has(page.id)) {
                            seenIds.add(page.id);
                            uniquePages.push(page);
                        } else {
                            duplicates.push({ index, id: page.id, name: page.name });
                        }
                    });

                    if (uniquePages.length !== sitemap.pages.length) {
                        console.warn(`⚠️ FOUND ${sitemap.pages.length - uniquePages.length} DUPLICATE PAGE(S)!`);
                        console.warn('🔍 Duplicate details:', duplicates);
                        sitemap.pages = uniquePages;

                        // SAVE CLEANED SITEMAP BACK TO LOCALSTORAGE
                        localStorage.setItem('currentSitemap', JSON.stringify(sitemap));
                        console.log('✅ Cleaned sitemap saved to localStorage');
                    }

                    console.log("📊 Final page count after dedup:", sitemap.pages.length);
                }

                window.stateManager.setSitemap(sitemap);

                // CRITICAL FIX: Manually trigger renderAllPages if wireframeEditor exists
                if (window.wireframeEditor && typeof window.wireframeEditor.renderAllPages === 'function') {
                    console.log('🎨 Manually triggering renderAllPages...');
                    window.wireframeEditor.renderAllPages(sitemap);
                }

                // Set default page for export (usually the first one)
                if (sitemap.pages && sitemap.pages.length > 0) {
                    // Small delay to ensure rendering is complete before visual feedback
                    setTimeout(() => {
                        this.selectPageForExport(sitemap.pages[0]);
                    }, 500);
                }
            } catch (e) {
                console.error("❌ Error parsing sitemap from localStorage:", e);
            }
        } else {
            console.warn("⚠️ No sitemap found in localStorage or StateManager missing");
            // Show empty state
            const board = document.getElementById('wireframeBoard');
            if (board) {
                board.innerHTML = `
                    <div class="empty-wireframe">
                        <h3>No pages found</h3>
                        <p>Create pages in the Sitemap view to see them here.</p>
                        <a href="index.html" class="btn btn-primary" style="margin-top: 20px;">Go to Sitemap</a>
                    </div>
                `;
            }
        }
    }

    bindEvents() {
        // Tab navigation (wireframe -> sitemap)
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.getAttribute('data-tab');
                if (tab === 'sitemap') {
                    window.location.href = 'index.html#editor';
                }
            });
        });

        // Export button toggle
        const exportPageBtn = document.getElementById('exportPageBtn');
        const exportDropdown = document.getElementById('exportDropdown');

        if (exportPageBtn && exportDropdown) {
            exportPageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                exportDropdown.style.display = exportDropdown.style.display === 'none' ? 'block' : 'none';
            });

            document.addEventListener('click', () => {
                exportDropdown.style.display = 'none';
            });
        }

        // Dropdown options
        document.querySelectorAll('.export-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const format = option.dataset.format;
                console.log(`📦 Format selected: ${format}`);
                if (['wp-elementor', 'react', 'html-css'].includes(format)) {
                    this.exportSpecificPage(format);
                } else {
                    const prettyName = this.getFormatName(format);
                    alert('Export for ' + prettyName + ' is coming soon.');
                }
            });
        });


        // Export All Button
        const exportAllBtn = document.getElementById('exportAllBtn');
        const generateAllBtn = document.getElementById('generateAllBtn');
        if (generateAllBtn) {
            generateAllBtn.addEventListener('click', () => {
                this.generateAllPages();
            });
        }
        if (exportAllBtn) {
            exportAllBtn.addEventListener('click', () => {
                this.exportAllPages();
            });
        }

        // Page Selection Logic (Event Delegation)
        document.addEventListener('click', (e) => {
            const column = e.target.closest('.wireframe-page-column');
            if (column && window.stateManager) {
                const pageId = column.dataset.pageId;
                const page = window.stateManager.findPageById(pageId);
                if (page) {
                    this.selectPageForExport(page);
                }
            }
        });
    }

    selectPageForExport(page) {
        this.selectedPageForExport = page;

        // Visual feedback
        document.querySelectorAll('.wireframe-page-column').forEach(col => {
            col.classList.remove('selected-for-export');
            if (col.dataset.pageId == page.id) {
                col.classList.add('selected-for-export');
            }
        });

        console.log("🎯 Selected page for export:", page.name);
    }

    async exportSpecificPage(format) {
        if (!this.selectedPageForExport) {
            alert('Please select a page first by clicking on it.');
            return;
        }

        console.log(`🚀 Starting export for: ${this.selectedPageForExport.name} in format: ${format}`);

        // Get latest page data from state manager
        if (window.stateManager) {
            const latestPage = window.stateManager.findPageById(this.selectedPageForExport.id);
            if (latestPage) {
                this.selectedPageForExport = latestPage;
            }
        }

        const page = this.selectedPageForExport;
        let content = '';
        let fileExtension = format === 'html-css' ? 'html' : 'json';
        const filename = `${(page.name || page.title || 'page').toLowerCase().replace(/\s+/g, '-')}-${format}.${fileExtension}`;

        if (format === 'wp-elementor') {
            const data = this.generateElementorFormat(page);
            content = JSON.stringify(data, null, 2);
        } else if (format === 'react') {
            await this.exportReactTailwindZIP(page);
            return; // JSZip handles download
        } else if (format === 'html-css') {
            try {
                content = await this.generateHTMLCSSFormat(page);
            } catch (error) {
                console.error("Export failed:", error);
                alert("Failed to generate HTML export. Check console for details.");
                return;
            }
        }

        if (!content) {
            console.error("Failed to generate content");
            return;
        }

        // Download
        const mimeType = format === 'html-css' ? 'text/html' : 'application/json';
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        console.log("✅ Export download triggered successfully.");
    }

    // --- HELPER: RGB TO HEX ---
    rgbToHex(rgb) {
        if (!rgb) return null;
        if (rgb.startsWith('#')) return rgb;
        if (rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return 'transparent';

        try {
            if (rgb.startsWith('rgba')) {
                const sep = rgb.indexOf(",") > -1 ? "," : " ";
                const parts = rgb.substring(5).split(")")[0].split(sep);
                if (parts.length >= 4) {
                    const alpha = parseFloat(parts[3]);
                    if (alpha === 0) return 'transparent';
                    if (alpha > 0 && alpha < 1) return rgb;
                }
                const r = parseInt(parts[0].trim()).toString(16).padStart(2, '0');
                const g = parseInt(parts[1].trim()).toString(16).padStart(2, '0');
                const b = parseInt(parts[2].trim()).toString(16).padStart(2, '0');
                return `#${r}${g}${b}`;
            }
            const sep = rgb.indexOf(",") > -1 ? "," : " ";
            const parts = rgb.substring(4).split(")")[0].split(sep);
            const r = parseInt(parts[0].trim()).toString(16).padStart(2, '0');
            const g = parseInt(parts[1].trim()).toString(16).padStart(2, '0');
            const b = parseInt(parts[2].trim()).toString(16).padStart(2, '0');
            return `#${r}${g}${b}`;
        } catch (e) {
            console.warn("Error converting RGB to Hex", rgb);
            return rgb;
        }
    }

    // --- HELPER: EXTRACT DIRECT TEXT ---
    extractDirectText(el) {
        if (!el) return '';
        let text = "";
        for (let node of el.childNodes) {
            if (node.nodeType === 3) {
                text += node.textContent;
            } else if (node.nodeType === 1) {
                const tagName = node.tagName.toLowerCase();
                const isBlock = ['p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName);
                if (!isBlock && !node.querySelector('p, div')) {
                    text += node.innerText;
                }
            }
        }
        return text.trim();
    }

    // --- ELEMENTOR EXPORT: FLEXBOX CONTAINER IMPLEMENTATION ---

    generateElementorFormat(page) {
        // 1. Get Global Styles
        // 1. Get Global Styles
        // FIX: Prioritize DOM > State Manager > Defaults
        // Previously, defaults were applying before State Manager could fill in the gaps if DOM was missing vars.

        const rootStyles = getComputedStyle(document.documentElement);

        // Helper to get defined value from precedence chain
        const resolveStyle = (cssVar, smKey, fallback) => {
            const domVal = rootStyles.getPropertyValue(cssVar).trim();
            if (domVal) return domVal;

            if (window.stateManager) {
                const sm = window.stateManager.getSitemap();
                if (sm && sm.styles && sm.styles[smKey]) return sm.styles[smKey];
            }

            return fallback;
        };

        // SPECIAL HANDLING FOR BUTTON COLOR (Primary Brand Color)
        // To strictly satisfy "color that is of 'get started' button", we try to find the button in the DOM.
        const getPhysicalButtonColor = () => {
            const btn = document.querySelector('.wireframe-section .cta-button, .wireframe-section button');
            if (btn) {
                const bg = getComputedStyle(btn).backgroundColor;
                if (bg && bg !== 'rgba(0, 0, 0, 0)') return this.rgbToHex(bg);
            }
            return null;
        };

        const resolvedBtnColor = resolveStyle('--wfe-btn-bg', 'btnColor', null) || getPhysicalButtonColor() || "#3b82f6";
        const resolvedTextColor = resolveStyle('--wfe-text-color', 'textColor', "#1f2937");

        const globalStyles = {
            primary: resolvedBtnColor,   // Brand Color
            secondary: resolvedTextColor,// Text Color
            accent: resolvedBtnColor,    // Accent (reusing Brand for now, unless we want a 3rd color)
            headingFont: resolveStyle('--wfe-font-heading', 'headingFont', "Inter, sans-serif"),
            paragraphFont: resolveStyle('--wfe-font-body', 'paragraphFont', "Inter, sans-serif"),
            backgroundColor: resolveStyle('--global-section-bg', 'backgroundColor', "transparent"),
            logoUrl: (window.stateManager?.getSitemap()?.styles?.logoUrl) || null
        };

        // Elementor Canvas Template (Blank Slate)
        const elementorData = {
            version: "0.4",
            title: page.name || page.title || "Exported Page",
            type: "page",
            content: [],
            page_settings: {
                template: "elementor_canvas",
                background_background: "classic",
                background_color: globalStyles.backgroundColor || "#fff7ed",
                custom_colors: {
                    primary: { title: "Primary", color: globalStyles.primary },
                    secondary: { title: "Secondary", color: globalStyles.secondary },
                    accent: { title: "Accent", color: globalStyles.accent }
                }
            },
            metadata: {
                template: "elementor_canvas",
                wp_page_template: "elementor_canvas"
            }
        };

        // Generate Containers for each section
        if (page.sections && page.sections.length > 0) {
            page.sections.forEach((section, index) => {
                const container = this.generateSectionContainer(section, index, globalStyles);
                elementorData.content.push(container);
            });
        }

        return elementorData;
    }

    // Generates the Main Section Container (Parent)
    generateSectionContainer(section, index, globalStyles) {
        const sectionId = `section-${index}`;
        const sectionType = (section.type || 'generic').toLowerCase();

        // --- CONTAINER SETTINGS ---
        const settings = {
            content_width: "boxed",
            width: { unit: "px", size: 1200 }, // Max-width 1200px
            gap: 20, // Default Gap

            // Flex Settings
            flex_direction: "column",
            justify_content: "center",
            align_items: "center",

            // Padding (Desktop)
            padding: { top: 80, right: 20, bottom: 80, left: 20, unit: "px", isLinked: false },

            // Padding (Mobile)
            padding_mobile: { top: 40, right: 16, bottom: 40, left: 16, unit: "px", isLinked: false },

            // Background
            background_background: "classic",
            background_color: section.styles?.backgroundColor || "transparent"
        };

        // --- CONTENT GENERATION ---
        const elements = this.generateContainerContent(section, sectionId, globalStyles, index);

        return {
            id: sectionId,
            elType: "container",
            settings: settings,
            elements: elements,
            isInner: false
        };
    }

    // Generates Internal Content (Widgets or Child Containers)
    generateContainerContent(section, sectionId, globalStyles, index) {
        // Use actual title/type from section
        const title = (section.title || '').toLowerCase();
        const sectionType = (section.type || '').toLowerCase();
        const variant = (section.layoutVariant || 'layout-default').toLowerCase();
        const content = [];

        // START: "WHAT YOU SEE IS WHAT YOU GET" (WYSIWYG) COLOR RESOLUTION
        // We attempt to find the ACTUAL DOM element for this section to read its computed CSS variables.
        // This bypasses any state desync issues and guarantees the export matches the visual.
        let computedSecondaryColor = null;
        let computedPrimaryColor = null;
        let computedBtnTextColor = null;

        try {
            // Find the element in the editor
            // We use the data-section-index attribute which aligns with our loop index
            const domEl = document.querySelector(`.wireframe-section[data-section-index="${index}"]`);
            if (domEl) {
                const style = getComputedStyle(domEl);
                computedSecondaryColor = style.getPropertyValue('--wfe-text-color').trim();
                computedPrimaryColor = style.getPropertyValue('--wfe-btn-bg').trim();
                computedBtnTextColor = style.getPropertyValue('--wfe-btn-text').trim();
                // console.log(`🎨 Section ${index} Visual Colors:`, { text: computedSecondaryColor, btn: computedPrimaryColor });
            }
        } catch (e) {
            console.warn("Could not read computed styles from DOM", e);
        }

        // Common Typography & Colors
        // PRIORITIZE: Visual DOM -> Section Styles -> Global Styles -> Default Fallbacks
        const sStyles = section.styles || {};

        const hFont = sStyles.headingFont || globalStyles.headingFont ? (sStyles.headingFont || globalStyles.headingFont).split(',')[0].replace(/['"]/g, '') : "Inter";
        const pFont = sStyles.paragraphFont || globalStyles.paragraphFont ? (sStyles.paragraphFont || globalStyles.paragraphFont).split(',')[0].replace(/['"]/g, '') : "Inter";

        // MAPPING USER SELECTED COLORS TO ROLES
        // MAPPING USER SELECTED COLORS TO ROLES
        // FOR HEADINGS AND TEXT: Enforce Global Color Bindings
        const primaryColor = "primary"; // Binds to custom_colors.primary
        const secondaryColor = "secondary"; // Binds to custom_colors.secondary
        const bodyColor = "secondary";

        // FOR BUTTONS & ICONS: Keep original Hex values (as requested "remain unchanged")
        const rawPrimaryHex = computedPrimaryColor || sStyles.btnColor || globalStyles.btnColor || "#3b82f6";
        const btnColor = rawPrimaryHex; // Use hex for buttons
        const btnTextColor = computedBtnTextColor || sStyles.btnTextColor || globalStyles.btnTextColor || "#ffffff";

        // --- 1. HERO SECTION ---
        if (sectionType === 'hero' || title.includes('welcome') || title.includes('intro')) {
            const hText = section.title || "Welcome";
            const dText = section.description || "Hero description here.";
            const bText = section.buttonText || "Get Started";

            // Reverting to SECONDARY COLOR (Text Color) for Hero Heading to match visual editor's H1 color
            const leftWidgets = [
                this.getWidget_Heading(`${sectionId}-h`, hText, "h1", hFont, 48, 600, "left"),
                this.getWidget_Text(`${sectionId}-t`, dText, pFont, 18, "left"),
                this.getWidget_Button(`${sectionId}-b`, bText)
            ];
            const rightWidgets = [this.getWidget_Image(`${sectionId}-img`, "https://via.placeholder.com/600x400")];

            // Layout Logic
            if (variant === 'layout-centered' || variant === 'centered' || variant === 'layout-minimal' || variant === 'layout-stacked') {
                // Centered/Stacked Layout
                const centerWidgets = [
                    this.getWidget_Heading(`${sectionId}-h`, hText, "h1", hFont, 48, 600, "center"),
                    this.getWidget_Text(`${sectionId}-t`, dText, pFont, 18, "center"),
                    this.getWidget_Button(`${sectionId}-b`, bText),
                    this.getWidget_Image(`${sectionId}-img`, "https://via.placeholder.com/600x400")
                ];
                if (variant === 'layout-minimal') centerWidgets.pop(); // Remove image for minimal
                content.push(this.createCenteredLayout(sectionId, centerWidgets));

            } else if (variant === 'layout-split-left' || variant === 'split-left') {
                // Image Left, Text Right
                content.push(this.createSplitLayout(sectionId, rightWidgets, leftWidgets)); // Swap sides
            } else {
                // Default: Image Right, Text Left (layout-split-right, layout-diagonal, layout-asymmetric)
                content.push(this.createSplitLayout(sectionId, leftWidgets, rightWidgets));
            }
        }

        // --- 2. NAVBAR ---
        else if (sectionType === 'navbar' || title.includes('nav')) {
            // Logic: Use section title directly. If empty, default to "Brand".
            // We do NOT force "Brand" if the user has "Navigation Bar" as the title.
            // The user's wireframe might say "Navigation Bar", so we export "Navigation Bar".
            let logoText = section.title || "Brand";

            const logoUrl = section.styles?.logoUrl || globalStyles.logoUrl;

            // Logo
            let logoWidget;
            if (logoUrl) {
                logoWidget = this.getWidget_Image(`${sectionId}-logo-img`, logoUrl, "150px");
            } else {
                logoWidget = this.getWidget_Heading(`${sectionId}-logo`, logoText, "h4", hFont, 24, 800, "left");
            }

            // Menu
            const defaultMenu = ['Home', 'About', 'Services', 'Contact'];
            const menuItems = section.menuItems || defaultMenu;
            const menuWidget = this.getWidget_IconList(`${sectionId}-menu`, menuItems, "row");

            if (variant === 'layout-centered-logo') {
                // [ Links ] [ Logo ] [ Links ]
                // Simulating with 3 cols provided manual split or just use basic 3 col layout
                const navContainer = {
                    id: `${sectionId}-nav-center`,
                    elType: "container",
                    settings: { content_width: "full", flex_direction: "row", justify_content: "space-between", align_items: "center", gap: 20 },
                    elements: [
                        // Left Menu
                        this.getWidget_IconList(`${sectionId}-menu-l`, menuItems.slice(0, 2), "row"),
                        // Center Logo
                        logoWidget,
                        // Right Menu
                        this.getWidget_IconList(`${sectionId}-menu-r`, menuItems.slice(2), "row")
                    ],
                    isInner: true
                };
                content.push(navContainer);

            } else if (variant === 'layout-split') {
                // [ Logo ] [ Links + Button ]
                const rightElements = [
                    menuWidget,
                    this.getWidget_Button(`${sectionId}-nav-btn`, "Sign In")
                ];
                const navContainer = {
                    id: `${sectionId}-nav-split`,
                    elType: "container",
                    settings: { content_width: "full", flex_direction: "row", justify_content: "space-between", align_items: "center" },
                    elements: [
                        logoWidget,
                        {
                            id: `${sectionId}-nav-right-grp`, elType: "container",
                            settings: { flex_direction: "row", gap: 16, align_items: "center", width: { unit: 'auto' } }, // Auto width for wrapper
                            elements: rightElements,
                            isInner: true
                        }
                    ],
                    isInner: true
                };
                content.push(navContainer);

            } else {
                // Default: Standard Horizontal [ Logo ] [ Links ] [ Button ]
                const navElements = [logoWidget, menuWidget];
                if (section.buttonText || title.includes('nav')) {
                    navElements.push(this.getWidget_Button(`${sectionId}-nav-btn`, section.buttonText || "Sign In"));
                }

                const navContainer = {
                    id: `${sectionId}-nav-row`,
                    elType: "container",
                    settings: { content_width: "full", flex_direction: "row", justify_content: "space-between", align_items: "center", min_height: { unit: "px", size: 80 }, gap: 20 },
                    elements: navElements,
                    isInner: true
                };
                content.push(navContainer);
            }
        }

        // --- 3. SPLIT CONTENT (Story, About, Mission, Vision) ---
        else if (title.includes('story') || title.includes('about') || title.includes('mission') || title.includes('vision') || title.includes('who we')) {
            const textWidgets = [
                this.getWidget_Heading(`${sectionId}-split-h`, section.title || "Our Story", "h2", hFont, 36, 600, "left"),
                this.getWidget_Text(`${sectionId}-split-t`, section.description || "Details about our specific journey...", pFont, 16, "left"),
                section.buttonText ? this.getWidget_Button(`${sectionId}-split-b`, section.buttonText) : null
            ].filter(Boolean);
            const imgWidgets = [this.getWidget_Image(`${sectionId}-split-img`, "https://via.placeholder.com/500x400")];

            if (variant === 'layout-split-left' || variant === 'split-left') {
                content.push(this.createSplitLayout(sectionId, imgWidgets, textWidgets));
            } else {
                content.push(this.createSplitLayout(sectionId, textWidgets, imgWidgets));
            }
        }

        // --- 4. MULTI-ITEM GRID (Team, Features, Services, Values, Culture) ---
        else if ((section.items && section.items.length > 0) || this.isGridSection(title)) {
            // Header
            content.push(this.getWidget_Heading(`${sectionId}-head`, section.title || "Section Title", "h2", hFont, 36, 600, "left"));
            // Remove subtitle for Services section to match target design
            if (section.description && !title.includes('service')) {
                content.push(this.getWidget_Text(`${sectionId}-sub`, section.description, pFont, 16, "center"));
            }
            content.push(this.getWidget_Spacer(40));

            const items = this.getMockItems(section);
            const isTeam = title.includes('team');
            const isServices = title.includes('service');

            // Calc Layout settings - Default to 2-column for Services
            let widthVal = isServices ? 45 : 31; // Services = 2-col grid (45% for safe fit), Others = 3-col
            if (variant.includes('grid-2')) widthVal = 44; // ~50%
            if (variant.includes('grid-3')) widthVal = 31; // ~33%
            if (variant.includes('grid-4')) widthVal = 23; // ~25%
            if (variant === 'layout-list' && !isServices) widthVal = 100; // Only allow list if NOT Services (Force Grid for services)

            const cardElements = items.map((item, i) => {
                const widgets = [];
                // Icon/Image
                if (isTeam) {
                    widgets.push(this.getWidget_Image(`${sectionId}-p-${i}`, "https://via.placeholder.com/120", "120px", true));
                } else if (variant !== 'layout-list' || isServices) {
                    widgets.push(this.getWidget_Icon(`${sectionId}-icon-${i}`, item.icon || "star"));
                }

                // Content - Left-align for Services, center for others
                const contentAlign = isServices ? "left" : "center";
                widgets.push(this.getWidget_Heading(`${sectionId}-ch-${i}`, item.title, "h3", hFont, 20, 600, contentAlign));
                widgets.push(this.getWidget_Text(`${sectionId}-ct-${i}`, item.desc, pFont, 14, contentAlign));

                // Container Wrapper
                return {
                    id: `${sectionId}-card-${i}`,
                    elType: "container",
                    settings: {
                        width: { unit: "%", size: widthVal },
                        width_tablet: { unit: "%", size: (widthVal > 40 ? 100 : 48) },
                        background_background: "classic",
                        background_color: isServices ? "transparent" : "#ffffff", // Services = Transparent, Others = White
                        padding: { unit: "px", top: 32, right: 24, bottom: 32, left: 24, isLinked: false },
                        border_radius: { unit: "px", top: 12, right: 12, bottom: 12, left: 12, isLinked: true },
                        // Remove box_shadow for Services to match snippet
                        ...(isServices ? {} : { box_shadow: { horizontal: 0, vertical: 4, blur: 20, color: "rgba(0,0,0,0.08)" } }),

                        flex_direction: variant === 'layout-list' ? "row" : "column",
                        gap: 16,
                        align_items: isServices ? "flex-start" : "center"
                    },
                    elements: widgets,
                    isInner: true
                };
            });

            const gridContainer = {
                id: `${sectionId}-grid`,
                elType: "container",
                settings: {
                    content_width: "full",
                    flex_direction: "row",
                    flex_wrap: "wrap",
                    gap: 20,
                    justify_content: "center",
                    align_items: "stretch"
                },
                elements: cardElements,
                isInner: true
            };
            content.push(gridContainer);
        }

        // --- 5. FOOTER ---
        else if (sectionType === 'footer') {
            // DYNAMIC FOOTER CONTENT from Wireframe Data
            const footerItems = section.items && section.items.length > 0 ? section.items : ['Company', 'Product', 'Resources', 'Legal'].map(t => ({ title: t, items: ["Link 1", "Link 2"] }));

            const footerCols = footerItems.map((col, i) => ({
                id: `${sectionId}-fcol-${i}`,
                elType: "container",
                settings: { width: { unit: "%", size: 100 / footerItems.length }, align_items: "start", gap: 16 },
                elements: [
                    this.getWidget_Heading(`${sectionId}-fh-${i}`, col.title || col, "h5", hFont, 18, 700, "left"),
                    this.getWidget_IconList(`${sectionId}-fl-${i}`, col.items || ["Link 1", "Link 2"], "list")
                ],
                isInner: true
            }));

            const footerRow = {
                id: `${sectionId}-footer-row`,
                elType: "container",
                settings: {
                    content_width: "full",
                    flex_direction: "row",
                    flex_wrap: "wrap",
                    gap: 30,
                    padding: { unit: "px", top: 60, right: 20, bottom: 60, left: 20, isLinked: false },
                    background_background: "classic",
                    background_color: "transparent" // MATCH WIREFRAME (No hardcoded dark bg)
                },
                elements: footerCols,
                isInner: true
            };
            return [footerRow];
        }

        // --- 6. GENERIC DEFAULT ---
        else {
            content.push(this.getWidget_Heading(`${sectionId}-def-h`, section.title || "Section", "h2", hFont, 32, 600, "center"));
            content.push(this.getWidget_Text(`${sectionId}-def-t`, section.description, pFont, 16, "center"));

            // If we have items but fell through to generic, try to render a grid
            if (section.items && section.items.length > 0) {
                // ... reuse grid logic or leave simple. For generic, simple is safer.
            }
        }

        return content;
    }

    // --- HELPER: CENTERED LAYOUT ---
    createCenteredLayout(idBase, widgets) {
        return {
            id: `${idBase}-centered-row`,
            elType: "container",
            settings: {
                content_width: "boxed",
                width: { unit: "px", size: 800 },
                flex_direction: "column",
                gap: 24,
                align_items: "center",
                justify_content: "center",
                text_align: "center"
            },
            elements: widgets,
            isInner: true
        };
    }

    // --- HELPER: SPLIT LAYOUT GENERATOR ---
    createSplitLayout(idBase, leftWidgets, rightWidgets) {
        return {
            id: `${idBase}-split-row`,
            elType: "container",
            settings: {
                content_width: "full",
                flex_direction: "row",
                gap: 50,
                align_items: "center"
            },
            elements: [
                {
                    id: `${idBase}-left`,
                    elType: "container",
                    settings: {
                        width: { unit: "%", size: 50 },
                        gap: 24,
                        padding: { unit: "px", top: 0, right: 0, bottom: 20, left: 0, isLinked: false },
                        flex_direction: "column",
                        align_items: "flex-start" // Ensure text aligns left in split
                    },
                    elements: leftWidgets,
                    isInner: true
                },
                {
                    id: `${idBase}-right`,
                    elType: "container",
                    settings: {
                        width: { unit: "%", size: 50 },
                        align_items: "center",
                        justify_content: "center"
                    },
                    elements: rightWidgets,
                    isInner: true
                }
            ],
            isInner: true
        };
    }

    // --- HELPER: WIDGET GENERATORS (UPDATED WITH COLOR/ALIGN) ---

    // --- HELPER: WIDGET GENERATORS (UPDATED FOR STRICT GLOBALS) ---

    getWidget_Heading(id, text, tag, font, size, weight, align = "left") {
        return {
            id: id, elType: "widget", widgetType: "heading",
            settings: {
                title: text, header_type: tag, align: align,
                typography_typography: "custom", typography_font_family: font,
                typography_font_size: { unit: "px", size: size },
                typography_font_weight: weight,
                text_color: "primary", // STRICT GLOBAL BINDING
                _margin: { unit: "px", top: 0, right: 0, bottom: 10, left: 0, isLinked: false }
            }
        };
    }

    getWidget_Text(id, text, font, size, align = "left") {
        return {
            id: id, elType: "widget", widgetType: "text-editor",
            settings: {
                editor: text || "Content goes here", align: align,
                typography_typography: "custom", typography_font_family: font,
                typography_font_size: { unit: "px", size: size },
                text_color: "secondary" // STRICT GLOBAL BINDING
            }
        };
    }

    getWidget_Button(id, text, align = "center") { // Removed bgColor argument
        return {
            id: id, elType: "widget", widgetType: "button",
            settings: {
                text: text, button_type: "default", size: "sm", align: align,
                button_text_color: "#ffffff", // Standard white text for buttons, or bind if needed
                background_color: "accent", // STRICT GLOBAL BINDING
                border_radius: { unit: "px", top: 6, right: 6, bottom: 6, left: 6, isLinked: true },
                padding: { unit: "px", top: 12, right: 28, bottom: 12, left: 28, isLinked: false }
            }
        };
    }

    getWidget_Image(id, url, width = null, isCircle = false) {
        const settings = { image: { url: url }, align: "center" };
        if (width) settings.width = { unit: "px", size: parseFloat(width) };
        if (isCircle) settings.style_image_radius = { unit: "%", top: 50, right: 50, bottom: 50, left: 50, isLinked: true };
        return { id: id, elType: "widget", widgetType: "image", settings: settings };
    }

    getWidget_Icon(id, iconName, color = "") {
        return {
            id: id, elType: "widget", widgetType: "icon",
            settings: {
                selected_icon: { value: `fas fa-${iconName}`, library: "fa-solid" },
                view: "default",
                primary_color: color || "accent" // Use Override color if present (for colorful services), else Strict Global Accent
            }
        };
    }

    getWidget_IconList(id, items, layout = "list") { // Removed color argument
        return {
            id: id, elType: "widget", widgetType: "icon-list",
            settings: {
                icon_list: items.map(t => ({ text: t })),
                view: layout === "row" ? "inline" : "list",
                text_color: "secondary", // STRICT GLOBAL BINDING
                icon_color: "accent" // Highlight icons in accent
            }
        };
    }

    getWidget_Spacer(height) {
        return {
            id: "spacer-" + Math.random(), elType: "widget", widgetType: "spacer",
            settings: { space: { unit: "px", size: height } }
        };
    }

    // --- HELPER: DATA MOCKING ---
    isGridSection(title) {
        return ['team', 'feature', 'service', 'value', 'culture', 'benefit', 'process'].some(k => title.includes(k));
    }

    getMockItems(section) {
        if (section.items && section.items.length > 0) return section.items;

        const title = (section.title || "").toLowerCase();
        if (title.includes('team')) {
            return [
                { title: "John Doe", desc: "CEO", icon: "user" },
                { title: "Jane Smith", desc: "CTO", icon: "user" },
                { title: "Mike Ross", desc: "Lead", icon: "user" },
                { title: "Sarah Lee", desc: "Design", icon: "user" }
            ];
        }
        return [
            { title: "Efficiency", desc: "Optimized workflows.", icon: "bolt" },
            { title: "Security", desc: "Top-tier protection.", icon: "lock" },
            { title: "Analytics", desc: "Data driven insights.", icon: "chart-bar" },
            { title: "Scalable", desc: "Grows with you.", icon: "expand" }
        ];
    }

    getFormatName(format) {
        const formatNames = {
            'wp-elementor': 'WordPress Elementor',
            'webflow': 'Webflow',
            'react': 'React & Tailwind',
            'html-css': 'HTML & CSS',
            'figma': 'Figma'
        };
        return formatNames[format] || format;
    }

    async generateAllPages() {
        const generateAllBtn = document.getElementById('generateAllBtn');
        const origText = generateAllBtn ? generateAllBtn.textContent : 'Generate All';
        if (generateAllBtn) {
            generateAllBtn.textContent = 'Generating...';
            generateAllBtn.disabled = true;
        }

        if (window.wireframeEditor && typeof window.wireframeEditor.showNotification === 'function') {
            window.wireframeEditor.showNotification('Generating wireframes for all pages...');
        }

        const sitemap = window.stateManager ? window.stateManager.getSitemap() : null;
        if (!sitemap || !sitemap.pages || sitemap.pages.length === 0) {
            alert('No pages found in sitemap.');
            if (generateAllBtn) {
                generateAllBtn.textContent = origText;
                generateAllBtn.disabled = false;
            }
            return;
        }

        try {
            const response = await fetch('/api/generate-wireframe/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sitemap_data: sitemap })
            });

            if (response.ok) {
                const data = await response.json();
                const wfPages = (data.wireframe && data.wireframe.pages) ? data.wireframe.pages : (data.pages || []);
                if (wfPages && wfPages.length > 0) {
                    wfPages.forEach(wfPage => {
                        const targetPage = sitemap.pages.find(p => p.id === wfPage.id || p.name === wfPage.name);
                        if (targetPage && wfPage.sections) {
                            targetPage.sections = wfPage.sections;
                        }
                    });
                    if (window.stateManager) {
                        window.stateManager.setSitemap(sitemap);
                        window.stateManager.saveToLocalStorage();
                    }
                    if (window.wireframeEditor) {
                        window.wireframeEditor.renderAllPages(sitemap);
                        window.wireframeEditor.showNotification('All pages generated successfully!');
                    }
                } else {
                    throw new Error('No wireframe pages returned by API');
                }
            } else {
                throw new Error(`API returned status ${response.status}`);
            }
        } catch (err) {
            console.warn('Backend generation failed or offline, falling back to local generator:', err);
            if (window.wireframeEditor && typeof window.wireframeEditor.generateFallbackWireframesForAllPages === 'function') {
                window.wireframeEditor.generateFallbackWireframesForAllPages();
            } else {
                alert('Generation failed and fallback editor unavailable.');
            }
        } finally {
            if (generateAllBtn) {
                generateAllBtn.textContent = origText;
                generateAllBtn.disabled = false;
            }
        }
    }

    async exportAllPages() {
        if (!window.JSZip) {
            alert('JSZip library not loaded. Cannot create ZIP.');
            return;
        }

        if (!window.stateManager || !window.stateManager.getSitemap()) {
            alert('No sitemap data to export.');
            return;
        }

        const sitemap = window.stateManager.getSitemap();
        const pages = sitemap.pages || [];

        if (pages.length === 0) {
            alert('No pages to export.');
            return;
        }

        const zip = new JSZip();

        // Loop through all pages and generate Elementor JSON
        pages.forEach(page => {
            const elementorData = this.generateElementorFormat(page);
            const filename = `${(page.name || 'page').toLowerCase().replace(/\s+/g, '-')}-elementor.json`;
            zip.file(filename, JSON.stringify(elementorData, null, 2));
        });

        // Add a Readme or info text logic if needed, but not strictly required by user.

        // Generate ZIP
        zip.generateAsync({ type: "blob" }).then(function (content) {
            const url = URL.createObjectURL(content);
            const a = document.createElement('a');
            a.href = url;
            a.download = "all-pages-elementor-export.zip";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 1000);
            console.log("✅ Export All complete. Zip downloaded.");
        });
    }

    // --- REACT & TAILWIND EXPORT IMPLEMENTATION (STRICT FIDELITY) ---

    async blobToBase64(url) {
        if (!url || url === 'none' || url.startsWith('data:')) return url;

        // Handle url("...") wrapper
        const cleanUrl = url.replace(/^url\(['"]?/, '').replace(/['"]?\)$/, '');

        // If it's not a blob or http url, return as is
        if (!cleanUrl.startsWith('blob:') && !cleanUrl.startsWith('http')) return cleanUrl;

        try {
            const response = await fetch(cleanUrl);
            const blob = await response.blob();
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    if (url.startsWith('url(')) {
                        resolve(`url("${reader.result}")`);
                    } else {
                        resolve(reader.result);
                    }
                };
                reader.onerror = () => resolve(url); // Fallback
                reader.readAsDataURL(blob);
            });
        } catch (e) {
            console.warn('Failed to convert image to base64', e);
            return url;
        }
    }

    async scrapePageFromDOM(page) {
        // Create a deep copy to avoid mutating the original state
        const capturedPage = JSON.parse(JSON.stringify(page));

        for (let index = 0; index < capturedPage.sections.length; index++) {
            const section = capturedPage.sections[index];
            // Find the actual DOM element for this section
            // We use the data-section-index attribute which aligns with our loop index
            // CRITICAL: We must scope this to the specific PAGE column, otherwise we might scrape the wrong page's section
            let el = document.querySelector(`.wireframe-page-column[data-page-id="${page.id}"] .wireframe-section[data-section-index="${index}"]`);

            // Fallback: If page ID lookup fails (e.g. type mismatch), try global search if only one page exists, or just log warn
            if (!el) {
                // Try searching loosely but warn
                const looseEl = document.querySelector(`.wireframe-section[data-section-index="${index}"]`);
                // Only use loose match if there's exactly one such element to avoid ambiguity
                if (looseEl && document.querySelectorAll(`.wireframe-section[data-section-index="${index}"]`).length === 1) {
                    el = looseEl;
                }
            }

            if (!el) {
                console.warn(`⚠️ Could not find DOM element for section ${index} on page ${page.id}. Scoping issue?`);
                // If we can't scrape styles, the export will look generic.
                // We should probably rely on state data, but the goal is WYSIWYG.
                // Let's at least initialize default styles so it doesn't crash.
                section.styles = section.styles || {};
                return;
            }

            // --- 1. CAPTURE COMPUTED STYLES (The "Strict" Part) ---
            const style = getComputedStyle(el);
            section.styles = section.styles || {};

            // Resolve Type for conditional logic
            const sectionType = (section.type || '').toLowerCase();
            const originalType = (section.meta && section.meta.originalType ? section.meta.originalType : '').toLowerCase();
            const typeToCheck = originalType || sectionType;

            // Background Color & Gradient
            section.styles.backgroundColor = this.rgbToHex(style.backgroundColor);
            section.styles.backgroundImage = style.backgroundImage !== 'none' ? style.backgroundImage : null;

            // Padding (Vertical)
            section.styles.paddingTop = style.paddingTop;
            section.styles.paddingBottom = style.paddingBottom;

            // Padding (Horizontal - typically on the inner container, but we capture section padding too)
            section.styles.paddingLeft = style.paddingLeft;
            section.styles.paddingRight = style.paddingRight;

            // Typography (Root for section)
            section.styles.color = this.rgbToHex(style.color);
            // RESET CONTENT: Trust DOM over any sitemap data for 100% fidelity
            section.title = '';
            section.description = '';
            section.buttonText = '';

            // --- 2. SCRAPE CONTENT WITH PRECISE SELECTORS ---

            // Title
            const titleEl = el.querySelector('[data-field="title"], h1, h2, .widget-heading, .section-title');
            if (titleEl) {
                section.title = titleEl.innerText.trim();
                const ts = getComputedStyle(titleEl);
                section.styles = {
                    ...section.styles,
                    titleColor: this.rgbToHex(ts.color),
                    titleFontSize: ts.fontSize,
                    titleFontWeight: ts.fontWeight,
                    titleAlign: ts.textAlign
                };
            }

            // Description - STRICT: Only if found in DOM
            // Narrow selector to avoid picking up item descriptions
            const descEl = el.querySelector('[data-field="description"], .section-header p, .section-description, .story-content, .description-text, :scope > p');
            if (descEl && descEl !== titleEl && !descEl.closest('.feature-item, .service-item, .blog-card, .team-item, .value-item, .member-card')) {
                let text = descEl.innerText.trim();
                // DEDUPE: If description starts with title, remove it
                if (section.title && text.startsWith(section.title)) {
                    text = text.substring(section.title.length).trim();
                }
                section.description = text;
                const ds = getComputedStyle(descEl);
                section.styles = {
                    ...section.styles,
                    descColor: this.rgbToHex(ds.color),
                    descFontSize: ds.fontSize,
                    descAlign: ds.textAlign
                };
            }

            // Button (CTA)
            const btnEl = el.querySelector('.cta-button, .btn, button, [data-field="button-text"], .section-button, .widget-button, .block-button, a[role="button"]');
            if (btnEl) {
                section.buttonText = btnEl.innerText.trim();
                const btnStyle = getComputedStyle(btnEl);

                // Get background color - check computed style and CSS var for robustness
                let bgHex = this.rgbToHex(btnStyle.backgroundColor);
                if (!bgHex || bgHex === 'transparent' || bgHex === 'rgba(0, 0, 0, 0)') {
                    const varBg = btnStyle.getPropertyValue('--wfe-btn-bg').trim();
                    if (varBg) bgHex = varBg.startsWith('rgb') ? this.rgbToHex(varBg) : varBg;
                }

                // Get text color - also check CSS var
                let textHex = this.rgbToHex(btnStyle.color);
                const varText = btnStyle.getPropertyValue('--wfe-btn-text').trim();
                if (varText) {
                    textHex = varText.startsWith('rgb') ? this.rgbToHex(varText) : varText;
                }

                section.styles.btnBg = bgHex;
                section.styles.btnTextColor = textHex;
                section.styles.btnRadius = btnStyle.borderRadius;
                section.styles.btnPadding = (btnStyle.paddingTop !== '0px' || btnStyle.paddingLeft !== '0px') ? `${btnStyle.paddingTop} ${btnStyle.paddingRight} ${btnStyle.paddingBottom} ${btnStyle.paddingLeft}` : undefined;

                // Also set btnColor for historical/editor compatibility (Background Color)
                section.styles.btnColor = bgHex;

                // SPECIAL: For contact forms, ensure the individual section styles object has btnBg
                section.styles.backgroundColor = section.styles.backgroundColor; // Ensure preserved
            }

            // --- NUCLEAR FALLBACK: If description is STILL empty but it's a content-heavy type ---
            if (!section.description && ['story', 'about', 'hero', 'cta', 'banner', 'location', 'map'].includes(typeToCheck)) {
                // Find any div or p with substantial text that isn't the title or a button
                // For location, we also look for address-like patterns or multiple small p/divs
                const isLocation = ['location', 'map'].includes(typeToCheck);
                const candidates = Array.from(el.querySelectorAll('div, p, span, section')).filter(cand => {
                    const text = cand.innerText.trim();
                    const rect = cand.getBoundingClientRect();
                    if (isLocation && text.length > 20 && cand !== titleEl && !cand.contains(titleEl)) return true;
                    return text.length > 50 && cand !== titleEl && !cand.contains(titleEl) && (!btnEl || !cand.contains(btnEl)) && rect.width > 200;
                });

                if (candidates.length > 0) {
                    // For location, we might want to join all candidates that look like address/contact info
                    if (isLocation) {
                        // FILTER candidates to avoid parent/child overlap (Redundant Text)
                        const filtered = candidates.filter(cand => {
                            return !candidates.some(other => other !== cand && cand.contains(other));
                        });
                        section.description = filtered.map(c => c.innerText.trim()).join('\n');
                    } else {
                        // Sort by text length descending
                        candidates.sort((a, b) => b.innerText.length - a.innerText.length);
                        section.description = candidates[0].innerText.trim();
                    }
                    console.log(`☢️ Nuclear fallback captured description for section ${index}:`, section.description.substring(0, 30) + '...');
                }
            }

            // Main Image (for Hero, Story, etc.)
            const mainImgEl = el.querySelector('[data-field="image"], .hero-image, .main-image, img.w-full.h-full.object-cover');
            if (mainImgEl && mainImgEl.tagName === 'IMG') {
                section.image = mainImgEl.getAttribute('src');
            }

            // --- 3. SCRAPE GRID/LIST ITEMS (Enhanced for nested containers) ---
            const noItemTypes = ['hero', 'story', 'cta', 'banner', 'newsletter', 'about', 'video'];

            // Only scrape items if it's NOT one of the excluded types
            // Exception: 'about' or 'contact' MIGHT have items if they are using a grid variant, but usually they are text.
            // For now, we'll exclude them to be safe, as they are causing issues. 
            // If the user specifically wants items in About, they should use a Features or component section.

            if (!noItemTypes.includes(typeToCheck)) {
                // SURGICAL DETECTION: Look for elements with data-item-index first
                let itemEls = Array.from(el.querySelectorAll('[data-item-index]'));

                // Fallback to legacy detection if no data-item-index found
                if (true) { // Nuclear Mode: Always search regardless of initial findings
                    let itemContainer = el.querySelector('.services-cards, .services-grid, .team-list, .team-grid, .team-cards, .culture-cards, .culture-grid, .features-grid, .pricing-grid, .blog-grid, .supporting-content-grid, .main-information-grid, .main-info-grid, .information-grid, .details-grid');
                    if (!itemContainer) itemContainer = el.querySelector('.grid, .flex, .section-content > div, [style*="display: grid"], [style*="display: flex"]');

                    if (itemContainer) {
                        // Find all potential cards/items anywhere inside the container
                        const standardItems = Array.from(itemContainer.querySelectorAll('.feature-item, .service-item, .team-item, .stat-item, .value-item, .gallery-item, .pricing-card, .blog-card, .support-card, .info-card, .main-info-card, .information-card, [class*="-item"], [class*="-card"]'));

                        // If standardItems failed or only found 1, let's look at the direct children of the lowest level container
                        let discoveryBase = itemContainer;
                        if (standardItems.length <= 1 && itemContainer.children.length === 1) {
                            // Possible wrapper div? Go one level deeper
                            const child = itemContainer.children[0];
                            if (child.children.length > 1) discoveryBase = child;
                        }

                        const directChildren = Array.from(discoveryBase.children).filter(child => {
                            return child.innerText.trim().length > 0 && !child.classList.contains('section-toolbar') && !child.classList.contains('toolbar');
                        });

                        // Combine and filter so we don't have parents and children in the same set
                        const candidates = [...new Set([...itemEls, ...standardItems, ...directChildren])];

                        // Filter out containers that have children which are also in the candidates list
                        itemEls = candidates.filter(cand => {
                            return !candidates.some(other => other !== cand && cand.contains(other));
                        });
                    }
                }

                if (itemEls.length > 0) {
                    const capturedItems = [];
                    itemEls.forEach((itemEl, i) => {
                        // 1. SELECTORS
                        let iconEl = itemEl.querySelector('.feature-icon, .icon, .emoji, [class*="icon"], .text-3xl, .text-4xl, .text-5xl, .text-6xl, i, svg');
                        // ... (keep iconEl fallback)
                        if (!iconEl) {
                            iconEl = Array.from(itemEl.querySelectorAll('div, span')).find(el => {
                                const fs = getComputedStyle(el).fontSize;
                                const bg = getComputedStyle(el).backgroundImage;
                                const rect = el.getBoundingClientRect();
                                const hasEmoji = /[\u{1F300}-\u{1F9FF}]/u.test(el.innerText.trim());
                                return (parseInt(fs) >= 16 && el.children.length === 0 && el.innerText.trim().length > 0) || (bg && bg !== 'none' && rect.width < 150 && rect.height < 150) || hasEmoji;
                            });
                        }

                        // 1. SELECTORS - TITLES
                        // Nuclear Fallback: If no h3-h5 or title class, just take the first div/span with text or first non-desc child
                        let itemTitleEl = itemEl.querySelector('[data-field="item-title"], h3, h4, h5, .font-bold, [class*="title"], .widget-heading');
                        if (!itemTitleEl) {
                            itemTitleEl = Array.from(itemEl.querySelectorAll('div, span, b, strong')).find(child => {
                                const ts = getComputedStyle(child);
                                return child.innerText.trim().length > 0 && parseInt(ts.fontWeight) >= 600;
                            });
                        }

                        let itemDescEl = itemEl.querySelector('[data-field="item-desc"]');
                        if (!itemDescEl) itemDescEl = Array.from(itemEl.querySelectorAll('p, .text-sm, .text-base, [class*="desc"], .widget-text')).find(el => el !== itemTitleEl);

                        // Improved dateEl: Target 12px text or specific classes, excludes title/desc
                        let dateEl = itemEl.querySelector('[data-field="item-date"], .blog-date, [class*="date"]');
                        if (!dateEl) {
                            // Fallback: Look for a div with small font-size that isn't title or desc
                            dateEl = Array.from(itemEl.querySelectorAll('div, span, p')).find(el => {
                                const fs = getComputedStyle(el).fontSize;
                                const text = el.innerText.trim();
                                return fs === '12px' && text.length > 0 && el !== itemTitleEl && el !== itemDescEl && !text.includes('Featured Image') && !text.includes('Image');
                            });
                        }

                        const avatarEl = itemEl.querySelector('.avatar, img, [class*="avatar"]');
                        const priceEl = itemEl.querySelector('[class*="price"], .price, .cost');

                        // 2. STYLES
                        const iStyle = getComputedStyle(itemEl);
                        const tStyle = itemTitleEl ? getComputedStyle(itemTitleEl) : {};
                        const dStyle = itemDescEl ? getComputedStyle(itemDescEl) : {};
                        const iconStyle = iconEl ? getComputedStyle(iconEl) : {};

                        // Capture item if it has ANY content (more lenient)
                        // VALIDATION: Ensure item is not just a container for the whole section (Redundant Text)
                        const itemText = itemEl.innerText.trim();
                        const sectionText = el.innerText.trim();
                        const isLikelyContainer = itemText.length > 50 && itemText.length > sectionText.length * 0.8;

                        if (!isLikelyContainer && (iconEl || avatarEl || itemTitleEl || itemDescEl || priceEl || itemText)) {

                            // Get icon text - check for FontAwesome class first, then text
                            let iconText = '';
                            if (iconEl) {
                                // 1. Try to find FontAwesome class (e.g. "fa-star")
                                let classes = Array.from(iconEl.classList);
                                let faClass = classes.find(c => c.startsWith('fa-') && c !== 'fa-solid' && c !== 'fa-regular' && c !== 'fa-brands' && c !== 'fa-duotone' && c !== 'fas' && c !== 'far' && c !== 'fab' && c !== 'fad');

                                // If not found on the element itself, check children (wrapper scenario)
                                if (!faClass) {
                                    const innerIcon = iconEl.querySelector('i[class*="fa-"], svg[class*="fa-"]');
                                    if (innerIcon) {
                                        classes = Array.from(innerIcon.classList);
                                        faClass = classes.find(c => c.startsWith('fa-') && c !== 'fa-solid' && c !== 'fa-regular' && c !== 'fa-brands' && c !== 'fa-duotone' && c !== 'fas' && c !== 'far' && c !== 'fab' && c !== 'fad');
                                    }
                                }

                                // Common FA to Lucide Mapping
                                const faToLucideMap = {
                                    'bullseye': 'Target', 'lightbulb': 'Lightbulb', 'rocket': 'Rocket', 'wrench': 'Wrench',
                                    'magic': 'Wand', 'shield': 'Shield', 'shield-alt': 'Shield', 'lock': 'Lock',
                                    'user': 'User', 'users': 'Users', 'check': 'Check', 'check-circle': 'CheckCircle',
                                    'times': 'X', 'times-circle': 'XCircle', 'plus': 'Plus', 'minus': 'Minus',
                                    'cog': 'Settings', 'cogs': 'Settings', 'envelope': 'Mail', 'paper-plane': 'Send',
                                    'comment': 'MessageSquare', 'comments': 'MessageSquare', 'heart': 'Heart', 'star': 'Star',
                                    'search': 'Search', 'home': 'Home', 'bars': 'Menu', 'bolt': 'Zap',
                                    'camera': 'Camera', 'video': 'Video', 'image': 'Image', 'map-marker-alt': 'MapPin',
                                    'map-marker': 'MapPin', 'calendar': 'Calendar', 'clock': 'Clock', 'bell': 'Bell',
                                    'chart-bar': 'BarChart', 'chart-pie': 'PieChart', 'dollar-sign': 'DollarSign', 'credit-card': 'CreditCard',
                                    'truck': 'Truck', 'box': 'Package', 'gift': 'Gift', 'tag': 'Tag',
                                    'globe': 'Globe', 'desktop': 'Monitor', 'mobile-alt': 'Smartphone', 'mobile': 'Smartphone',
                                    'laptop': 'Laptop', 'server': 'Server', 'database': 'Database', 'wifi': 'Wifi',
                                    'thumbs-up': 'ThumbsUp', 'thumbs-down': 'ThumbsDown', 'arrow-right': 'ArrowRight', 'arrow-left': 'ArrowLeft',
                                    'chevron-right': 'ChevronRight', 'chevron-left': 'ChevronLeft', 'chevron-down': 'ChevronDown', 'chevron-up': 'ChevronUp',
                                    'play': 'Play', 'pause': 'Pause'
                                };

                                if (faClass) {
                                    const rawName = faClass.replace('fa-', '').toLowerCase();
                                    iconText = faToLucideMap[rawName] || rawName.split('-').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('');
                                } else if (iconEl.tagName === 'IMG') {
                                    // Skip
                                } else {
                                    iconText = iconEl.innerText.trim() || iconEl.textContent.trim() || '';
                                }

                                // VALIDATION: Icons should be short (Lucide names or emojis)
                                if (iconText.length > 50) iconText = '';
                            }

                            // 3. Final Fallback: If we found an icon element but couldn't extract name, default to 'Star'
                            if (!iconText && iconEl && iconEl.tagName !== 'IMG') {
                                iconText = 'Star';
                            }

                            // Capture Role/Position - EXCLUDE image placeholders
                            const roleEl = itemEl.querySelector('.role, .position, [class*="role"], [class*="position"]');
                            let role = '';
                            if (roleEl && roleEl !== itemTitleEl && roleEl !== itemDescEl && roleEl !== iconEl && roleEl !== dateEl) {
                                let roleText = roleEl.innerText.trim();
                                // De-concatenate: subtract other fields if roleEl contains them
                                [itemTitleEl, itemDescEl, iconEl, dateEl].forEach(other => {
                                    if (other && roleEl.contains(other) && other !== roleEl) {
                                        const otherText = other.innerText.trim();
                                        if (otherText && roleText.includes(otherText)) {
                                            roleText = roleText.replace(otherText, '').trim();
                                        }
                                    }
                                });
                                if (roleText && !roleText.includes('Featured Image') && !roleText.includes('Image') && roleText.length < 100) {
                                    role = roleText;
                                }
                            }

                            // Detect "Popular" tag
                            const isPopular = Array.from(itemEl.querySelectorAll('*')).some(el => {
                                const text = el.innerText.trim().toUpperCase();
                                return text === 'POPULAR' || text === 'MOST POPULAR' || text === 'BEST VALUE';
                            }) || itemEl.classList.contains('popular') || itemEl.classList.contains('featured');

                            // Capture item button text and style
                            const bEl = itemEl.querySelector('button, .btn, [class*="button"], [class*="btn"]');
                            const bText = bEl ? bEl.innerText.trim() : '';
                            let bStyle = null;
                            if (bEl) {
                                const bs = getComputedStyle(bEl);
                                bStyle = {
                                    backgroundColor: this.rgbToHex(bs.backgroundColor),
                                    color: this.rgbToHex(bs.color),
                                    borderRadius: bs.borderRadius,
                                    padding: bs.padding,
                                    fontSize: bs.fontSize,
                                    fontWeight: bs.fontWeight
                                };
                            }

                            // Item specific card styles
                            const iStyle = getComputedStyle(itemEl);
                            const cardStyle = {
                                backgroundColor: this.rgbToHex(iStyle.backgroundColor),
                                borderColor: this.rgbToHex(iStyle.borderColor),
                                borderWidth: iStyle.borderWidth,
                                borderRadius: iStyle.borderRadius,
                                padding: iStyle.padding
                            };

                            // Capture Title/Description styles
                            const tStyle = itemTitleEl ? getComputedStyle(itemTitleEl) : {};
                            const dStyle = itemDescEl ? getComputedStyle(itemDescEl) : {};

                            capturedItems.push({
                                icon: iconEl ? iconText : (avatarEl ? 'avatar' : ''),
                                iconStyle: iconEl ? {
                                    backgroundColor: this.rgbToHex(iconStyle.backgroundColor),
                                    color: this.rgbToHex(iconStyle.color),
                                    fontSize: iconStyle.fontSize,
                                    textAlign: iconStyle.textAlign,
                                    borderRadius: iconStyle.borderRadius
                                } : null,
                                avatarSrc: avatarEl ? (avatarEl.getAttribute('src') || avatarEl.style.backgroundImage || '') : null,
                                title: (() => {
                                    if (!itemTitleEl) return '';
                                    // Use innerText but subtract ALL other detected content to avoid concatenation
                                    let text = itemTitleEl.innerText.trim();
                                    [itemDescEl, dateEl, priceEl, iconEl].forEach(other => {
                                        if (other && other !== itemTitleEl && itemTitleEl.contains(other)) {
                                            const otherText = other.innerText.trim();
                                            if (otherText && text.includes(otherText)) {
                                                text = text.replace(otherText, '').trim();
                                            }
                                        }
                                    });
                                    // Fallback to direct text if replacement left nothing or if it looks suspicious
                                    if (!text) text = this.extractDirectText(itemTitleEl);
                                    return text;
                                })(),
                                titleStyle: itemTitleEl ? { color: this.rgbToHex(tStyle.color), fontSize: tStyle.fontSize, textAlign: tStyle.textAlign, fontWeight: tStyle.fontWeight } : null,
                                desc: (itemDescEl && itemDescEl !== itemTitleEl) ? itemDescEl.innerText.trim() : '',
                                descStyle: itemDescEl ? { color: this.rgbToHex(dStyle.color), fontSize: dStyle.fontSize, textAlign: dStyle.textAlign } : null,
                                role: role,
                                date: dateEl ? dateEl.innerText.trim() : '',
                                price: priceEl ? priceEl.innerText.trim() : null,
                                priceStyle: priceEl ? { color: this.rgbToHex(getComputedStyle(priceEl).color) } : null,
                                buttonText: bText,
                                buttonStyle: bStyle,
                                cardStyle: {
                                    backgroundColor: (this.rgbToHex(iStyle.backgroundColor) === 'transparent' || (this.rgbToHex(iStyle.backgroundColor) === '#000000' && iStyle.backgroundColor === 'rgba(0, 0, 0, 0)')) ? '#ffffff' : this.rgbToHex(iStyle.backgroundColor),
                                    borderColor: (this.rgbToHex(iStyle.borderColor) === '#000000' || this.rgbToHex(iStyle.borderColor) === 'transparent') ? 'transparent' : this.rgbToHex(iStyle.borderColor),
                                    borderWidth: iStyle.borderWidth,
                                    borderRadius: iStyle.borderRadius,
                                    paddingTop: iStyle.paddingTop,
                                    paddingBottom: iStyle.paddingBottom,
                                    paddingLeft: iStyle.paddingLeft,
                                    paddingRight: iStyle.paddingRight,
                                    textAlign: iStyle.textAlign,
                                    display: iStyle.display,
                                    flexDirection: iStyle.flexDirection,
                                    alignItems: iStyle.alignItems,
                                    justifyContent: iStyle.justifyContent,
                                    gap: iStyle.gap
                                },
                                isPopular: isPopular
                            });
                        }
                    });

                    // Only override if we actually found items
                    if (capturedItems.length > 0) {
                        section.items = capturedItems;
                        // 100% Fidelity: If we found items, their parent is the definitive content container for layout
                        const firstItem = itemEls[0];
                        if (firstItem && firstItem.parentElement) {
                            const container = firstItem.parentElement;
                            const cs = getComputedStyle(container);
                            section.styles.display = cs.display;
                            section.styles.gridTemplateColumns = (cs.gridTemplateColumns && cs.gridTemplateColumns !== 'none') ? cs.gridTemplateColumns : undefined;
                            section.styles.gap = (cs.gap && cs.gap !== 'normal') ? cs.gap : undefined;
                            section.styles.flexDirection = cs.flexDirection;
                            section.styles.alignItems = cs.alignItems;
                            section.styles.justifyContent = cs.justifyContent;

                            // Propagate card background to section styles for tailwind mapping
                            const itemBg = capturedItems[0].cardStyle.backgroundColor;
                            if (itemBg && itemBg !== 'transparent') {
                                section.styles.itemBg = itemBg;
                            }
                        }
                        console.log(`✅ Captured ${capturedItems.length} items for section: ${section.title}`);
                    }
                }

            } // End of noItemTypes check

            // --- 4. DETECT LAYOUT MODE ---
            // Check for grid vs flex - look for specific item container classes first
            const contentContainer =
                el.querySelector('.team-list, .team-grid, .team-cards') ||
                el.querySelector('.culture-cards, .culture-grid') ||
                el.querySelector('.pricing-card, .pricing-grid, .pricing-cards') ||
                el.querySelector('.gallery-item, .gallery-grid') ||
                el.querySelector('.blog-card, .blog-grid') ||
                el.querySelector('.stat-item, .stats-grid') ||
                el.querySelector('.testimonial-card, .testimonial-grid') ||
                el.querySelector('.services-cards, .services-grid, .features-grid, .main-information-grid') ||
                el.querySelector('.section-content > div') ||
                el.querySelector('.grid, .flex, [style*="display: grid"], [style*="display: flex"]') ||
                el.querySelector('.wireframe-element');

            if (contentContainer) {
                const computed = getComputedStyle(contentContainer);
                section.styles.display = computed.display;
                section.styles.gridTemplateColumns = (computed.gridTemplateColumns && computed.gridTemplateColumns !== 'none') ? computed.gridTemplateColumns : undefined;
                section.styles.gap = (computed.gap && computed.gap !== 'normal') ? computed.gap : undefined;
                section.styles.flexDirection = computed.flexDirection;
                section.styles.alignItems = computed.alignItems;
                section.styles.justifyContent = computed.justifyContent;

                console.log(`📐 Layout detection for "${section.title}":`, {
                    container: contentContainer.className,
                    display: computed.display,
                    gridCols: section.styles.gridTemplateColumns,
                    gap: section.styles.gap
                });
            }

            console.log(`🔍 [Section ${index} Scrape]`, {
                title: section.title,
                bgScraped: section.styles.backgroundColor,
                elContext: el
            });

            // --- 5. ASYNC ASSET CONVERSION (Strict Fidelity) ---
            if (section.styles.backgroundImage) {
                section.styles.backgroundImage = await this.blobToBase64(section.styles.backgroundImage);
            }

            if (section.image) {
                section.image = await this.blobToBase64(section.image);
            }

            if (section.items && section.items.length > 0) {
                for (const item of section.items) {
                    if (item.avatarSrc) item.avatarSrc = await this.blobToBase64(item.avatarSrc);
                    if (item.image) item.image = await this.blobToBase64(item.image);
                }
            }
        }

        return capturedPage;
    }

    // --- HELPER: COMPREHENSIVE ELEMENT STYLE SCRAPER ---
    scrapeCompleteElementStyles(element) {
        if (!element) return {};

        const computed = getComputedStyle(element);

        return {
            // Layout
            display: computed.display,
            position: computed.position,
            flexDirection: computed.flexDirection,
            flexWrap: computed.flexWrap,
            alignItems: computed.alignItems,
            justifyContent: computed.justifyContent,
            gap: computed.gap,
            gridTemplateColumns: computed.gridTemplateColumns,
            gridTemplateRows: computed.gridTemplateRows,

            // Spacing
            padding: computed.padding,
            paddingTop: computed.paddingTop,
            paddingRight: computed.paddingRight,
            paddingBottom: computed.paddingBottom,
            paddingLeft: computed.paddingLeft,
            margin: computed.margin,
            marginTop: computed.marginTop,
            marginRight: computed.marginRight,
            marginBottom: computed.marginBottom,
            marginLeft: computed.marginLeft,

            // Sizing
            width: computed.width,
            height: computed.height,
            maxWidth: computed.maxWidth,
            maxHeight: computed.maxHeight,
            minWidth: computed.minWidth,
            minHeight: computed.minHeight,

            // Colors
            color: this.rgbToHex(computed.color),
            backgroundColor: this.rgbToHex(computed.backgroundColor),
            backgroundImage: computed.backgroundImage,
            backgroundSize: computed.backgroundSize,
            backgroundPosition: computed.backgroundPosition,
            backgroundRepeat: computed.backgroundRepeat,

            // Typography
            fontFamily: computed.fontFamily,
            fontSize: computed.fontSize,
            fontWeight: computed.fontWeight,
            lineHeight: computed.lineHeight,
            letterSpacing: computed.letterSpacing,
            textAlign: computed.textAlign,
            textTransform: computed.textTransform,
            textDecoration: computed.textDecoration,

            // Borders
            border: computed.border,
            borderWidth: computed.borderWidth,
            borderStyle: computed.borderStyle,
            borderColor: this.rgbToHex(computed.borderColor),
            borderRadius: computed.borderRadius,

            // Effects
            boxShadow: computed.boxShadow,
            opacity: computed.opacity,
            transform: computed.transform,
            transition: computed.transition
        };
    }

    // --- HELPER: COMPUTED STYLES TO TAILWIND CONVERTER ---
    computedStylesToTailwind(styles) {
        const classes = [];
        const inlineStyles = {};

        // Helper to convert px values to Tailwind arbitrary values
        const pxToArbitrary = (value) => {
            if (!value || value === 'auto' || value === 'none' || value === '0px') return null;
            // Keep the exact value for arbitrary syntax
            return value;
        };

        // Layout
        if (styles.display) {
            if (styles.display === 'flex') {
                classes.push('flex');
                if (styles.flexDirection === 'column') classes.push('flex-col');
                if (styles.flexDirection === 'row-reverse') classes.push('flex-row-reverse');
                if (styles.flexDirection === 'column-reverse') classes.push('flex-col-reverse');

                // Flex alignment
                const alignMap = {
                    'center': 'items-center',
                    'flex-start': 'items-start',
                    'flex-end': 'items-end',
                    'stretch': 'items-stretch',
                    'baseline': 'items-baseline'
                };
                if (alignMap[styles.alignItems]) classes.push(alignMap[styles.alignItems]);

                const justifyMap = {
                    'center': 'justify-center',
                    'flex-start': 'justify-start',
                    'flex-end': 'justify-end',
                    'space-between': 'justify-between',
                    'space-around': 'justify-around',
                    'space-evenly': 'justify-evenly'
                };
                if (justifyMap[styles.justifyContent]) classes.push(justifyMap[styles.justifyContent]);

                if (styles.flexWrap === 'wrap') classes.push('flex-wrap');
            } else if (styles.display === 'grid') {
                classes.push('grid');
                // Grid columns - use arbitrary value for exact match
                if (styles.gridTemplateColumns && styles.gridTemplateColumns !== 'none') {
                    inlineStyles.gridTemplateColumns = styles.gridTemplateColumns;
                }
            } else if (styles.display === 'block') {
                classes.push('block');
            } else if (styles.display === 'inline-block') {
                classes.push('inline-block');
            }
        }

        // Gap - use arbitrary value for exact spacing
        if (styles.gap && styles.gap !== 'normal' && styles.gap !== '0px') {
            const gapValue = pxToArbitrary(styles.gap);
            if (gapValue) classes.push(`gap-[${gapValue}]`);
        }

        // Padding - use arbitrary values for exact spacing
        if (styles.paddingTop && styles.paddingTop !== '0px') {
            classes.push(`pt-[${styles.paddingTop}]`);
        }
        if (styles.paddingBottom && styles.paddingBottom !== '0px') {
            classes.push(`pb-[${styles.paddingBottom}]`);
        }
        if (styles.paddingLeft && styles.paddingLeft !== '0px') {
            classes.push(`pl-[${styles.paddingLeft}]`);
        }
        if (styles.paddingRight && styles.paddingRight !== '0px') {
            classes.push(`pr-[${styles.paddingRight}]`);
        }

        // Width & Height
        if (styles.width && styles.width !== 'auto') {
            if (styles.width === '100%') {
                classes.push('w-full');
            } else {
                classes.push(`w-[${styles.width}]`);
            }
        }

        if (styles.maxWidth && styles.maxWidth !== 'none') {
            classes.push(`max-w-[${styles.maxWidth}]`);
        }

        // Text alignment
        const textAlignMap = {
            'left': 'text-left',
            'center': 'text-center',
            'right': 'text-right',
            'justify': 'text-justify'
        };
        if (textAlignMap[styles.textAlign]) {
            classes.push(textAlignMap[styles.textAlign]);
        }

        // Font weight
        if (styles.fontWeight) {
            const weight = parseInt(styles.fontWeight);
            if (weight >= 700) classes.push('font-bold');
            else if (weight >= 600) classes.push('font-semibold');
            else if (weight >= 500) classes.push('font-medium');
        }

        // Border radius
        if (styles.borderRadius && styles.borderRadius !== '0px') {
            classes.push(`rounded-[${styles.borderRadius}]`);
        }

        // Box shadow
        if (styles.boxShadow && styles.boxShadow !== 'none') {
            // Use inline style for exact shadow
            inlineStyles.boxShadow = styles.boxShadow;
        }

        // Colors - always use inline styles for exact color matching
        if (styles.color && styles.color !== 'transparent') {
            inlineStyles.color = styles.color;
        }
        if (styles.backgroundColor && styles.backgroundColor !== 'transparent') {
            inlineStyles.backgroundColor = styles.backgroundColor;
        }
        if (styles.backgroundImage && styles.backgroundImage !== 'none') {
            inlineStyles.backgroundImage = styles.backgroundImage;
            inlineStyles.backgroundSize = styles.backgroundSize;
            inlineStyles.backgroundPosition = styles.backgroundPosition;
        }

        // Typography - use inline styles for exact matching
        if (styles.fontFamily) {
            inlineStyles.fontFamily = styles.fontFamily;
        }
        if (styles.fontSize) {
            inlineStyles.fontSize = styles.fontSize;
        }
        if (styles.lineHeight && styles.lineHeight !== 'normal') {
            inlineStyles.lineHeight = styles.lineHeight;
        }
        if (styles.letterSpacing && styles.letterSpacing !== 'normal') {
            inlineStyles.letterSpacing = styles.letterSpacing;
        }

        // Border
        if (styles.borderWidth && styles.borderWidth !== '0px') {
            inlineStyles.border = `${styles.borderWidth} ${styles.borderStyle} ${styles.borderColor}`;
        }

        return {
            classes: classes.join(' '),
            styles: inlineStyles
        };
    }

    // --- HELPER: LAYOUT STRUCTURE DETECTOR ---
    detectLayoutStructure(element) {
        if (!element) return { type: 'block', structure: {} };

        const computed = getComputedStyle(element);
        const display = computed.display;

        if (display === 'grid') {
            return {
                type: 'grid',
                structure: {
                    columns: computed.gridTemplateColumns,
                    rows: computed.gridTemplateRows,
                    gap: computed.gap,
                    alignItems: computed.alignItems,
                    justifyItems: computed.justifyItems
                }
            };
        } else if (display === 'flex') {
            return {
                type: 'flex',
                structure: {
                    direction: computed.flexDirection,
                    wrap: computed.flexWrap,
                    alignItems: computed.alignItems,
                    justifyContent: computed.justifyContent,
                    gap: computed.gap
                }
            };
        } else {
            return {
                type: 'block',
                structure: {
                    textAlign: computed.textAlign
                }
            };
        }
    }

    async generateReactTailwindFormat(pageInput) {
        // 1. Scrape latest content from DOM to ensure WYSIWYG
        const page = await this.scrapePageFromDOM(pageInput);

        // 2. Resolve Global Colors precisely from CSS Variables (Fallback)
        const getVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        const globalStyles = {
            colors: {
                primary: getVar('--wfe-btn-bg') || "#3b82f6",
                text: getVar('--wfe-text-color') || "#1f2937",
                background: getVar('--global-section-bg') || "#ffffff",
                accent: getVar('--wfe-btn-bg') || "#3b82f6",
                gradient: getComputedStyle(document.documentElement).background || null
            },
            fonts: {
                heading: "Inter", // We use arbitrary values mostly now, but keep as fallback
                body: "Inter"
            }
        };

        // 3. Map Page Structure
        const reactData = {
            version: "1.0",
            framework: "React",
            styling: "Tailwind CSS",
            page: {
                id: page.id,
                name: page.name || "Unnamed Page",
                layout: "vertical-stack",
                globalStyles: globalStyles,
                sections: (page.sections || []).map((section, index) => this.mapSectionToReactTailwind(section, index, globalStyles))
            }
        };

        return reactData;
    }

    mapSectionToReactTailwind(section, index, global) {
        const type = (section.type || 'generic').toLowerCase();
        const variant = (section.layoutVariant || 'layout-default').toLowerCase();
        const title = (section.title || '');

        // Resolve specialized component type
        let resolvedType = this.translateToReactComponent(type, title);

        let component = {
            id: `section-${index}`,
            type: resolvedType,
            variant: variant,
            meta: {
                title: section.title,
                description: section.description,
                index: index,
                originalType: type
            },
            styles: section.styles || {}
        };

        // Enrich based on Resolved Type
        switch (resolvedType) {
            case 'Navbar':
                component = this.enrichNavbarReact(component, section);
                break;
            case 'HeroSection':
                component = this.enrichHeroReact(component, section);
                break;
            case 'Testimonials':
                component = this.enrichTestimonialsReact(component, section);
                break;
            case 'PricingSection':
                component = this.enrichPricingSectionReact(component, section);
                break;
            case 'FeaturesGrid':
                component = this.enrichFeaturesGridReact(component, section);
                break;
            case 'BlogSection':
                component = this.enrichBlogSectionReact(component, section);
                break;
            case 'StackSection':
                component = this.enrichStackSectionReact(component, section);
                break;
            case 'FeaturesList':
                component = this.enrichFeaturesListReact(component, section);
                break;
            case 'Footer':
                component = this.enrichFooterReact(component, section, global);
                break;
            case 'GallerySection':
                component = this.enrichGalleryReact(component, section);
                break;
            case 'CTASection':
                component = this.enrichCTASectionReact(component, section);
                break;
            case 'StatsSection':
                component = this.enrichStatsReact(component, section);
                break;
            case 'MapSection':
                component = this.enrichMapReact(component, section);
                break;
            case 'PricingSection':
                component = this.enrichPricingReact(component, section);
                break;
            case 'ContactSection':
                component = this.enrichContactReact(component, section);
                break;
            default:
                component = this.enrichUniversalReact(component, section);
        }

        return component;
    }

    translateToReactComponent(type, title) {
        const lowerTitle = title.toLowerCase();
        const lowType = (type || '').toLowerCase();

        if (lowType === 'faq' || lowerTitle.includes('faq') || lowerTitle.includes('question')) return 'FAQSection';
        if (lowType === 'product-grid' || lowType === 'products' || lowerTitle.includes('product') || lowerTitle.includes('catalog')) return 'ProductGrid';
        if (lowType === 'services' || lowType === 'services-grid' || lowerTitle.includes('service')) return 'ServicesGrid';
        if (lowType === 'team' || lowerTitle.includes('team') || lowerTitle.includes('leadership')) return 'TeamSection';
        if (lowType === 'about' || lowerTitle.includes('about') || lowerTitle.includes('story') || lowType === 'story') return 'AboutSection';
        if (lowType === 'image-text') return 'ImageTextSection';
        if (lowType === 'process' || lowerTitle.includes('process') || lowerTitle.includes('how it works')) return 'ProcessSection';
        if (lowType === 'sidebar' || lowerTitle.includes('sidebar')) return 'SidebarSection';

        if (lowType === 'hero' || lowerTitle.includes('hero')) return 'HeroSection';
        if (lowType === 'navbar' || lowerTitle.includes('nav')) return 'Navbar';
        if (lowType === 'footer' || lowerTitle.includes('footer')) return 'Footer';
        if (lowType === 'testimonial' || lowerTitle.includes('testimonial')) return 'Testimonials';
        if (lowType === 'pricing' || lowerTitle.includes('pricing')) return 'PricingSection';
        if (lowType === 'blog' || lowerTitle.includes('blog')) return 'BlogSection';
        if (lowType === 'gallery' || lowerTitle.includes('gallery') || lowerTitle.includes('portfolio')) return 'GallerySection';
        if (lowType === 'cta' || lowerTitle.includes('call to action') || lowerTitle.includes('cta')) return 'CTASection';
        if (lowType === 'stack' || lowerTitle.includes('stack')) return 'StackSection';
        if (lowType === 'stats' || lowerTitle.includes('stats') || lowerTitle.includes('numbers')) return 'StatsSection';
        if (lowType === 'location' || lowType === 'map' || lowerTitle.includes('location') || lowerTitle.includes('map')) return 'MapSection';
        if (lowType === 'services' || lowerTitle.includes('services')) return 'FeaturesGrid';

        // "Key Features" often looks better as a List if it has small icons, or Grid if large cards
        // Defaulting "List" to FeaturesList is safer for horizontal layouts
        if (lowerTitle.includes('list') || lowType.includes('list') || lowType.includes('team') || lowType.includes('meet the team')) return 'FeaturesList';
        if (lowerTitle.includes('key features')) return 'FeaturesList'; // PREFER LIST for Key Features based on user feedback
        if (lowType === 'contact' || lowerTitle.includes('contact form')) return 'ContactSection';
        if (lowerTitle.includes('our story') || lowType === 'story') return 'FeaturesGrid';

        if (lowerTitle.includes('supporting') || lowerTitle.includes('content')) return 'FeaturesList';
        if (lowerTitle.includes('main info') || lowerTitle.includes('information')) return 'FeaturesGrid';

        return 'FeaturesGrid';
    }

    // --- ENRICHERS WITH STRICT ARBITRARY VALUES ---

    enrichHeroReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-split-right').toLowerCase().replace('layout-', '');

        comp.content = {
            heading: sec.title || "Welcome to Our Site",
            subtext: sec.description || "Unlock your potential with our cutting-edge solutions designed for growth and efficiency.",
            cta: sec.buttonText || "Get Started",
            image: sec.image || null
        };

        const formatColor = (color, fallback) => {
            const c = color || fallback;
            if (c === 'transparent') return fallback;
            return c.startsWith('#') ? c : `#${c}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#e8d5c4');
        const bgImage = s.backgroundImage;
        const headingColor = formatColor(s.titleColor, '#3d2817');
        const subtextColor = formatColor(s.descColor, '#7a6f66');

        // Button Colors - Be robust to both scraper (btnBg, btnTextColor) and editor (btnColor, btnTextColor) names
        const btnBg = formatColor(s.btnBg || s.btnColor, '#3b82f6');
        const btnColor = formatColor(s.btnTextColor, '#ffffff'); // Use btnTextColor exclusively for text

        // Layout Mapping
        let sectionClass = `w-full py-[80px] px-6`;
        let innerClass = `max-w-[1200px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-[64px] items-center`;
        let textClass = `flex flex-col`;
        let headingClass = `text-[48px] leading-[56px] font-[700] mb-[24px]`;
        let subtextClass = `text-[16px] leading-[24px] font-[400] mb-[32px] max-w-[480px]`;
        let mockupContainerClass = `flex justify-center items-center`;
        let mockupClass = `w-[480px] h-[360px] rounded-[16px] flex items-center justify-center text-[18px] font-[500]`;

        if (variant === 'centered' || variant === 'bold-text') {
            innerClass = `max-w-[1200px] mx-auto flex flex-col items-center text-center gap-[48px]`;
            textClass = `flex flex-col items-center`;
            subtextClass = `text-[16px] leading-[24px] font-[400] mb-[32px] max-w-[600px]`;
            if (variant === 'bold-text') {
                headingClass = `text-[64px] leading-[1.1] font-[800] mb-[24px]`;
            }
        } else if (variant === 'split-left') {
            textClass = `flex flex-col md:order-last`; // Swap text to right
        } else if (variant === 'stacked') {
            innerClass = `max-w-[1200px] mx-auto flex flex-col items-center text-center gap-[64px]`;
            mockupClass = `w-full max-w-[700px] h-[400px] rounded-[16px] flex items-center justify-center text-[18px] font-[500]`;
        } else if (variant === 'minimal') {
            innerClass = `max-w-[1200px] mx-auto flex flex-col items-start gap-[24px] py-[60px]`;
            mockupContainerClass = `hidden`;
        } else if (variant === 'full-bg') {
            sectionClass = `w-full py-[120px] px-6 relative flex items-center justify-center`;
            innerClass = `max-w-[800px] mx-auto text-center z-10`;
            mockupContainerClass = `hidden`;
        } else if (variant === 'video-bg' || variant === 'asymmetric') {
            innerClass = `max-w-[1200px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-center`;
            if (variant === 'asymmetric') {
                innerClass = `max-w-[1200px] mx-auto grid grid-cols-1 md:grid-cols-3 gap-12 items-center`;
                textClass = `md:col-span-2`;
            }
        }

        comp.tailwind = {
            section: sectionClass,
            sectionStyle: {
                backgroundColor: bgColor,
                backgroundImage: bgImage,
                backgroundSize: 'cover',
                backgroundPosition: 'center'
            },
            inner: innerClass,
            textWrapper: textClass,
            heading: headingClass,
            headingStyle: { color: headingColor },
            subtext: subtextClass,
            subtextStyle: { color: subtextColor },
            button: `inline-block rounded-[4px] px-[20px] py-[8px] text-[16px] font-[600] leading-[24px] w-auto transition-all hover:scale-105 active:scale-95 shadow-sm`,
            buttonStyle: { backgroundColor: btnBg, color: btnColor },
            mockupContainer: mockupContainerClass,
            mockup: mockupClass,
            mockupStyle: { backgroundColor: '#f5f5f5', color: '#9ca3af' }
        };

        return comp;
    }

    enrichFeaturesGridReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-grid-3').toLowerCase();

        // Filter out empty placeholder items
        const filteredItems = (sec.items || []).filter(item => item.title || item.desc || item.icon);

        comp.content = {
            title: sec.title,
            description: sec.description || "",
            items: filteredItems
        };

        // CLEANUP: Final dedupe of title from description for high fidelity
        if (comp.content.title && comp.content.description.startsWith(comp.content.title)) {
            comp.content.description = comp.content.description.substring(comp.content.title.length).replace(/^[\\n\\r\\s]+/, '');
        }

        // FORCE HIGH FIDELITY STYLES for Story/About
        const isStory = ['story', 'about'].includes((sec.meta?.originalType || '').toLowerCase());
        if (isStory) {
            comp.styles.titleAlign = 'center';
            comp.styles.descAlign = 'center';
            if (!comp.styles.titleFontSize || comp.styles.titleFontSize === '0px') comp.styles.titleFontSize = '48px';
            if (!comp.styles.titleFontWeight || comp.styles.titleFontWeight === '0') comp.styles.titleFontWeight = '800';
            if (!comp.styles.descFontSize || comp.styles.descFontSize === '0px') comp.styles.descFontSize = '1.25rem';
        }

        // FORCE RESPONSIVE GRID - Ignore fixed pixel widths, use responsive classes
        let gridClass = `grid grid-cols-1 md:grid-cols-3 gap-8`;

        // Detect intended column count from variant or style, but MAP TO TAILWIND CLASS
        const gridCols = s.gridTemplateColumns;
        let colCount = 3;

        if (gridCols && gridCols !== 'none' && gridCols.includes('px')) {
            const colParts = gridCols.trim().split(/\s+/);
            if (colParts.length > 0) colCount = colParts.length;
        } else if (gridCols && gridCols !== 'none') {
            const repeatMatch = gridCols.match(/repeat\((\d+)/);
            if (repeatMatch) colCount = parseInt(repeatMatch[1]);
            else colCount = gridCols.trim().split(/\s+/).length;
        } else {
            if (variant.includes('grid-2')) colCount = 2;
            if (variant.includes('grid-4')) colCount = 4;
        }

        gridClass = `grid grid-cols-1 md:grid-cols-${colCount} gap-8`;
        if (colCount === 1 || ['story', 'about'].includes((sec.meta?.originalType || '').toLowerCase())) gridClass = `grid grid-cols-1 gap-8`;
        else if (colCount === 2) gridClass = `grid grid-cols-1 md:grid-cols-2 gap-8`;
        else if (colCount === 4) gridClass = `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8`;

        let innerClass = `max-w-7xl mx-auto`;
        if (variant === 'layout-list') {
            gridClass = `flex flex-col gap-6`;
            innerClass = `max-w-4xl mx-auto`;
        } else if (variant === 'layout-cards') {
            // High Fidelity: If multiple columns were detected visually, keep the grid!
            if (colCount > 1) {
                // gridClass is already set based on colCount
            } else {
                gridClass = `flex flex-col gap-6`;
                innerClass = `max-w-4xl mx-auto`;
            }
        } else if (variant === 'layout-horizontal') {
            gridClass = `flex gap-8 overflow-x-auto pb-8 snap-x`;
            innerClass = `max-w-full px-6`;
        }

        const formatColor = (color, fallback) => {
            if (!color || color === 'transparent') return fallback;
            return color.startsWith('#') ? color : `#${color}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#ffffff');
        const titleColor = formatColor(s.titleColor, '#2c3e50');
        const descColor = formatColor(s.descColor, '#5a6c7d');

        const titleAlign = s.titleAlign || 'center';
        const descAlign = s.descAlign || 'center';
        const itemAlign = s.itemAlign || s.titleAlign || 'center';

        comp.tailwind = {
            section: `w-full py-20 px-6`,
            sectionStyle: {
                backgroundColor: bgColor,
                backgroundImage: s.backgroundImage || 'none',
                backgroundSize: 'cover',
                paddingTop: s.paddingTop || '80px',
                paddingBottom: s.paddingBottom || '80px'
            },
            inner: innerClass,
            header: `text-${titleAlign} mb-12`,
            title: `text-4xl font-bold mb-4 text-${titleAlign}`,
            titleStyle: { color: titleColor },
            desc: `text-lg mb-8 max-w-2xl ${titleAlign === 'center' ? 'mx-auto' : ''} text-${descAlign}`,
            descStyle: { color: descColor },
            grid: gridClass,
            card: `bg-white rounded-xl shadow-md hover:shadow-lg transition-all p-8 text-${itemAlign}`,
            icon: `text-5xl mb-4`,
            itemTitle: `text-xl font-semibold mb-2`,
            itemTitleStyle: { color: titleColor },
            itemDesc: `text-base text-gray-500`,
            itemDescStyle: { color: descColor }
        };
        return comp;
    }

    enrichMapReact(comp, sec) {
        const s = comp.styles;

        comp.content = {
            title: sec.title || "Our Location",
            address: sec.description || "123 Main Street, City, State 12345\nPhone: +1 (555) 123-4567\nEmail: hello@company.com",
            mockup: {
                label: "Map",
                icon: "Map"
            }
        };

        // Capture high-fidelity colors
        const titleColor = s.titleColor || s.color || '#4b3f2f';
        const descColor = s.color || '#5a6c7d';

        comp.tailwind = {
            section: `w-full py-20 px-6`,
            sectionStyle: {
                backgroundColor: s.backgroundColor || '#e9d8a6',
                paddingTop: s.paddingTop || '80px',
                paddingBottom: s.paddingBottom || '80px'
            },
            inner: `max-w-7xl mx-auto flex flex-col items-center`,
            header: `text-center mb-10 w-full`,
            title: `text-[32px] font-bold mb-4`,
            titleStyle: { color: titleColor },
            desc: `text-[1.1rem] leading-relaxed opacity-90 text-center space-y-2`,
            descStyle: { color: descColor },
            mockupWrapper: `w-full max-w-5xl mx-auto mb-12 aspect-[21/9] md:aspect-[3/1]`,
            mockupStyle: {
                backgroundColor: '#dbeafe', // Light blue map-like background
                borderRadius: '24px',
                border: '1px solid #bfdbfe'
            }
        };

        return comp;
    }

    enrichContactReact(comp, sec) {
        const s = comp.styles;

        comp.content = {
            title: sec.title || "Contact Form",
            description: sec.description || "",
            form: {
                fields: [
                    { label: "Name", type: "text", placeholder: "Enter your name" },
                    { label: "Email", type: "email", placeholder: "Enter your email" },
                    { label: "Message", type: "textarea", placeholder: "How can we help?" }
                ],
                button: sec.buttonText || "Send Message"
            },
            sidebar: {
                items: [
                    { title: "Address", icon: "📍", desc: "123 Business St, Suite 100\nCity, State 12345" },
                    { title: "Email", icon: "✉️", desc: "contact@company.com" },
                    { title: "Phone", icon: "📞", desc: "+1 (555) 123-4567" }
                ],
                mockup: { label: "Map", icon: "Map" }
            }
        };

        // If we have scraped items, try to map them to sidebar info
        const validItems = (sec.items || []).filter(item => (item.title && item.title.trim()) || (item.desc && item.desc.trim()));
        if (validItems.length > 0) {
            comp.content.sidebar.items = validItems.map(item => {
                let title = item.title || "";
                let icon = item.icon || "Info";
                let desc = item.desc || "";

                // SMART PARSING: If title starts with emoji, extract it as icon
                const emojiMatch = title.match(/^([\u{1F300}-\u{1F9FF}]|.)\s*(.*)/u);
                if (emojiMatch && /[\u{1F300}-\u{1F9FF}]/u.test(emojiMatch[1])) {
                    icon = emojiMatch[1];
                    title = emojiMatch[2].trim();
                }

                // If icon is a huge chunk of text (scraping fail), default to Info
                if (icon.length > 50) icon = "Info";

                // DE-DUPE: If description starts with title, clean it
                if (title && desc.startsWith(title)) {
                    desc = desc.replace(title, '').trim();
                }

                return { title, icon, desc };
            });
        }

        // Apply high-fidelity styles
        comp.styles.titleAlign = 'start';
        if (!comp.styles.titleFontSize || comp.styles.titleFontSize === '0px') comp.styles.titleFontSize = '32px';
        if (!comp.styles.titleFontWeight || comp.styles.titleFontWeight === '0') comp.styles.titleFontWeight = '700';

        // Ensure button styles are preserved for the template
        // Force blue button if it's the brown fallback from the editor
        if (s.btnBg === '#8b5e34' || s.btnColor === '#8b5e34') {
            s.btnBg = '#6366f1';
            s.btnColor = '#6366f1';
        }
        comp.styles.btnBg = s.btnBg || s.btnColor || '#3b82f6';
        comp.styles.btnTextColor = s.btnTextColor || '#ffffff';

        // Add tailwind layout properties for the exported JSON
        comp.tailwind = {
            section: `w-full py-20 px-6`,
            sectionStyle: {
                backgroundColor: s.backgroundColor || '#e9d8a6',
                paddingTop: s.paddingTop || '80px',
                paddingBottom: s.paddingBottom || '80px'
            },
            inner: `max-w-7xl mx-auto`,
            title: `text-[32px] font-bold mb-4`,
            titleStyle: { color: s.titleColor || s.color || '#4b3f2f' }
        };

        return comp;
    }

    enrichFeaturesListReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-list').toLowerCase().replace('layout-', '');

        // Filter out empty placeholder items
        const filteredItems = (sec.items || []).filter(item => item.title || item.desc || item.icon);

        comp.content = {
            title: sec.title,
            description: "",
            items: filteredItems
        };

        // Layout Mapping
        const gridCols = s.gridTemplateColumns;
        let colCount = 1;
        if (gridCols && gridCols !== 'none') {
            colCount = gridCols.trim().split(/\s+/).length;
        }

        let innerClass = `max-w-7xl mx-auto px-6`;
        let listClass = (colCount > 1) ? `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-${colCount} gap-8` : `flex flex-col gap-6`;
        let cardClass = `flex items-start gap-6 p-6 rounded-xl border border-gray-100`;

        if (variant.includes('grid-2')) {
            listClass = `grid grid-cols-1 md:grid-cols-2 gap-8`;
        } else if (variant.includes('grid-3')) {
            listClass = `grid grid-cols-1 md:grid-cols-3 gap-8`;
        } else if (variant.includes('grid-4')) {
            listClass = `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8`;
        } else if (variant === 'carousel') {
            listClass = `flex gap-6 overflow-x-auto pb-6 snap-x snap-mandatory hide-scrollbar`;
            cardClass = `flex-shrink-0 w-80 snap-start flex flex-col items-center gap-4 p-6 rounded-xl border border-gray-100`;
            innerClass = `max-w-7xl mx-auto px-6 overflow-hidden`;
        } else if (variant === 'centered') {
            innerClass = `max-w-4xl mx-auto px-6 text-center`;
            cardClass = `flex flex-col items-center gap-4 p-6 rounded-xl border border-gray-100`;
        }

        comp.tailwind = {
            section: `w-full py-20 px-6`,
            inner: innerClass,
            header: `text-center mb-12`,
            title: `text-4xl font-bold mb-4`,
            list: listClass,
            card: cardClass,
            iconWrapper: `flex-shrink-0 flex items-center justify-center rounded-lg text-2xl`,
            itemContent: `flex flex-col flex-1 gap-1`,
            itemTitle: `text-lg font-bold mb-2`,
            itemDesc: `text-base text-gray-500`
        };
        return comp;
    }

    enrichNavbarReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-horizontal').toLowerCase().replace('layout-', '');

        comp.content = {
            logo: sec.title || "Brand",
            links: sec.menuItems || ['Home', 'About', 'Services', 'Contact'],
            cta: sec.buttonText || null // Valid: only if text exists
        };

        const formatColor = (color, fallback) => {
            const c = color || fallback;
            if (c === 'transparent') return 'transparent';
            return c.startsWith('#') ? c : `#${c}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#ffffff');
        const bgImage = s.backgroundImage;
        const titleColor = formatColor(s.titleColor, '#1f2937');
        const textColor = formatColor(s.color, '#4b5563');

        // Support both editor and export naming conventions
        const btnBg = formatColor(s.btnBg || s.btnColor, '#3b82f6');
        const btnColor = formatColor(s.btnTextColor, '#ffffff');

        // Layout Mapping
        let innerClass = `max-w-7xl mx-auto flex justify-between items-center px-6 h-full`;
        let logoClass = `text-2xl font-bold transition-colors hover:text-blue-600`;
        let linksClass = `flex gap-8 items-center`;

        const lowerVariant = variant.toLowerCase();
        if (lowerVariant === 'centered-logo' || lowerVariant.includes('centered')) {
            innerClass = `max-w-7xl mx-auto grid grid-cols-3 items-center px-6 h-full`;
            logoClass = `text-center text-2xl font-bold order-2`;
            // Split links for centered logo
            const links = comp.content.links || [];
            const mid = Math.ceil(links.length / 2);
            comp.content.splitLinks = {
                left: links.slice(0, mid),
                right: links.slice(mid)
            };
        } else if (lowerVariant === 'minimal') {
            innerClass = `max-w-4xl mx-auto flex justify-between items-center px-6 h-full`;
        } else if (lowerVariant === 'split' || lowerVariant === 'classic horizontal' || lowerVariant.includes('horizontal') || lowerVariant.includes('classic')) {
            // CLASSIC HORIZONTAL: Logo Left, Links Right
            innerClass = `w-full max-w-[1400px] mx-auto flex justify-between items-center px-8 h-full`;
            linksClass = `flex gap-10 items-center justify-end flex-1`;
        }

        // Detect Capsule Mode
        const navRadius = parseInt(s.borderRadius || '0');
        const isCapsule = navRadius > 20 || s.borderRadius === '9999px';

        comp.tailwind = {
            nav: `w-full h-20 border-b border-gray-100 sticky top-0 z-50 transition-all flex items-center ${isCapsule ? 'px-4 mt-4' : ''}`,
            navStyle: {
                backgroundColor: bgColor,
                backgroundImage: bgImage || 'none',
                backgroundSize: 'cover',
                padding: isCapsule ? '0 32px' : '0 24px',
                borderRadius: s.borderRadius || '0px',
                width: isCapsule ? 'calc(100% - 32px)' : '100%',
                margin: isCapsule ? '16px auto' : '0'
            },
            inner: innerClass,
            logo: logoClass,
            logoStyle: { color: titleColor },
            links: linksClass,
            link: `text-base font-medium transition-colors hover:text-blue-500`,
            linkStyle: { color: textColor },
            button: `px-5 py-2.5 rounded-lg text-sm font-semibold transition-all hover:opacity-90 active:scale-95 shadow-sm inline-flex items-center justify-center whitespace-nowrap`,
            buttonStyle: { backgroundColor: btnBg, color: btnColor }
        };
        return comp;
    }

    enrichFooterReact(comp, sec, global) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-default').toLowerCase().replace('layout-', '');

        // Use scraped items if available, otherwise fallback to defaults
        const defaultColumns = [
            { title: "Company", links: ["About Us", "Careers", "Press", "Blog"] },
            { title: "Product", links: ["Features", "Pricing", "Security", "Updates"] },
            { title: "Resources", links: ["Documentation", "Guides", "API", "Support"] },
            { title: "Legal", links: ["Privacy", "Terms", "Cookies", "Licenses"] }
        ];

        comp.content = {
            brand: sec.title || "Footer",
            copyright: "© 2024 Company Name. All rights reserved.",
            columns: []
        };

        // Capture copyright specifically from DOM if possible
        const footerEl = document.querySelector(`.wireframe-page-column[data-page-id="${sec.id || comp.id}"] .wireframe-section[data-section-index="${sec.meta?.index || 0}"]`);
        if (footerEl) {
            const copyEl = footerEl.querySelector('.copyright, [data-field="copyright"], .footer-bottom p');
            if (copyEl) comp.content.copyright = copyEl.innerText.trim();
        }

        // Resolve columns: use scraped items if they look valid, otherwise use high-fidelity defaults
        let resolvedColumns = null;
        if (sec.items && sec.items.length > 0) {
            // FILTER: Remove items that look like copyright or are too small
            const filteredItems = sec.items.filter(item => {
                const text = (item.desc || item.title || '').toLowerCase();
                if (text.includes('©') || text.includes('copyright') || text.includes('all rights reserved')) return false;
                return true;
            });

            resolvedColumns = this.mapScrapedItemsToColumns(filteredItems);
            // Validation: if we only got empty columns, discard them
            if (resolvedColumns && resolvedColumns.every(col => col.links.length === 0)) {
                resolvedColumns = null;
            }
        }

        if (resolvedColumns) {
            comp.content.columns = resolvedColumns;
        } else {
            comp.content.columns = defaultColumns;
        }

        const formatColor = (color, fallback) => {
            const c = color || fallback;
            if (c === 'transparent') return fallback;
            return c.startsWith('#') ? c : `#${c}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#f8fafc');
        const bgImage = s.backgroundImage;
        const colTitleColor = formatColor(s.titleColor, '#5c4a3d');
        const textColor = formatColor(s.descColor, '#64748b');

        // Button Styles for Newsletter
        const btnBg = formatColor(s.btnBg || s.btnColor, '#8b5e34');
        const btnTextColor = formatColor(s.btnTextColor, '#ffffff');

        // Layout Mapping
        let innerClass = `max-w-7xl mx-auto px-6`;
        let gridClass = `grid grid-cols-2 md:grid-cols-4 gap-8`;

        if (variant === 'centered') {
            innerClass = `max-w-4xl mx-auto px-6 text-center py-12`;
            gridClass = `flex flex-wrap justify-center gap-x-12 gap-y-4 mb-8`;
        } else if (variant === 'minimal' || variant === 'bar') {
            innerClass = `max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center py-8 border-t border-gray-100`;
            gridClass = `flex gap-6 mt-4 md:mt-0`;
        } else if (variant === 'newsletter') {
            innerClass = `max-w-7xl mx-auto px-6 py-16`;
            gridClass = `grid grid-cols-2 md:grid-cols-4 gap-8`;
            comp.content.newsletter = {
                title: "Stay Updated",
                description: "Subscribe to our newsletter for the latest updates",
                buttonText: sec.buttonText || "Subscribe",
                buttonStyle: {
                    backgroundColor: btnBg,
                    color: btnTextColor,
                    borderRadius: s.btnRadius || '4px'
                }
            };
        }

        comp.tailwind = {
            footer: `w-full px-6`,
            footerStyle: {
                backgroundColor: bgColor,
                backgroundImage: bgImage || 'none',
                backgroundSize: 'cover',
                paddingTop: s.paddingTop || '80px',
                paddingBottom: s.paddingBottom || '40px',
                marginTop: s.marginTop || '0px',
                marginBottom: s.marginBottom || '0px'
            },
            inner: innerClass,
            grid: `grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-12`,
            colTitle: `text-lg font-bold mb-6`,
            colTitleStyle: { color: colTitleColor },
            link: `text-sm transition-colors hover:opacity-80 block mb-3`,
            linkStyle: { color: textColor },
            brand: `text-2xl font-bold mb-4`,
            brandStyle: { color: formatColor(s.titleColor, '#1f2937') },
            copyright: `text-sm pt-8 border-t border-gray-200/20 text-center`,
            copyrightStyle: { color: textColor }
        };
        return comp;
    }

    mapScrapedItemsToColumns(items) {
        // Logic to group scraped items into columns if they follow a list pattern
        // For now, we'll try to reconstruct a few columns from the flat list
        const cols = [];
        const chunkSize = Math.ceil(items.length / 4);
        for (let i = 0; i < items.length; i += chunkSize) {
            const chunk = items.slice(i, i + chunkSize);
            cols.push({
                title: chunk[0]?.title || "Navigation",
                links: chunk.map(item => item.desc || item.title).filter(Boolean)
            });
        }
        return cols.length > 0 ? cols : null;
    }

    enrichGenericReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-default').toLowerCase().replace('layout-', '');
        comp.content = { title: sec.title, text: sec.description };

        const formatColor = (color, fallback) => {
            const c = color || fallback;
            if (c === 'transparent') return fallback;
            return c.startsWith('#') ? c : `#${c}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#ffffff');
        const bgImage = s.backgroundImage;
        const titleColor = formatColor(s.titleColor, '#000000');
        const textColor = formatColor(s.descColor, '#666666');

        // Layout Mapping
        let innerClass = `max-w-4xl mx-auto px-6 text-center`;
        if (variant === 'split') {
            innerClass = `max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center text-left`;
        } else if (variant === 'minimal') {
            innerClass = `max-w-4xl mx-auto px-6 text-left py-12`;
        }

        comp.tailwind = {
            section: `w-full py-20`,
            sectionStyle: {
                backgroundColor: bgColor,
                backgroundImage: bgImage || 'none',
                backgroundSize: 'cover'
            },
            inner: innerClass,
            title: `text-4xl font-bold mb-6`,
            titleStyle: { color: titleColor },
            text: `text-lg`,
            textStyle: { color: textColor }
        };
        return comp;
    }

    enrichStatsReact(comp, sec) {
        // Use universal for base styles
        comp = this.enrichUniversalReact(comp, sec);

        // Stats specific: ensure titles are large and colors are correct
        const s = comp.styles;
        const titleColor = s.titleColor || '#2c3e50';

        comp.tailwind.itemTitle = `text-4xl md:text-5xl font-extrabold mb-2`;
        comp.tailwind.itemTitleStyle = { color: titleColor };
        comp.tailwind.itemDesc = `text-sm uppercase tracking-wider font-semibold opacity-70`;

        // Force grid for stats
        comp.tailwind.grid = `grid grid-cols-2 lg:grid-cols-4 gap-8`;

        return comp;
    }

    // --- UNIVERSAL SECTION ENRICHMENT (Dynamic for ANY section type) ---
    enrichUniversalReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-default').toLowerCase();

        comp.content = {
            title: sec.title || '',
            description: sec.description || '',
            buttonText: sec.buttonText || null,
            items: sec.items || []
        };

        let gridClass = `grid grid-cols-1 md:grid-cols-3 gap-8`;
        let innerClass = `max-w-7xl mx-auto`;

        const gridCols = s.gridTemplateColumns;
        let colCount = 3;

        if (gridCols && gridCols !== 'none') {
            const repeatMatch = gridCols.match(/repeat\((\d+|auto-fit|auto-fill),\s*([^)]+)\)/);
            if (repeatMatch) {
                const repeatCount = repeatMatch[1];
                colCount = (repeatCount === 'auto-fit' || repeatCount === 'auto-fill') ? 4 : parseInt(repeatCount, 10);
            } else {
                colCount = gridCols.trim().split(/\s+/).length;
            }

            if (colCount === 2) gridClass = `grid grid-cols-1 md:grid-cols-2 gap-8`;
            else if (colCount === 3) gridClass = `grid grid-cols-1 md:grid-cols-3 gap-8`;
            else if (colCount === 4) gridClass = `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8`;
            else if (colCount >= 5) gridClass = `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-${colCount} gap-8`;
        } else if (s.display === 'flex') {
            if (s.flexDirection === 'column' || variant === 'layout-list' || variant.includes('list')) {
                gridClass = `flex flex-col gap-6`;
                innerClass = `max-w-4xl mx-auto`;
            } else if (variant === 'layout-horizontal' || variant.includes('horizontal')) {
                gridClass = `flex gap-8 overflow-x-auto pb-8`;
                innerClass = `max-w-full px-6`;
            } else {
                gridClass = `flex flex-wrap gap-8`;
            }
        } else if (s.display === 'block') {
            gridClass = `block`;
        }

        if (variant === 'layout-list' || variant.includes('list')) {
            gridClass = `flex flex-col gap-6`;
            innerClass = `max-w-4xl mx-auto`;
        } else if (variant === 'layout-horizontal' || variant.includes('horizontal')) {
            gridClass = `flex gap-8 overflow-x-auto pb-8`;
            innerClass = `max-w-full px-6`;
        }

        comp.tailwind = {
            section: `w-full py-20 px-6`,
            inner: innerClass,
            header: `text-center mb-12`,
            title: `text-4xl font-bold mb-4`,
            grid: gridClass,
            card: `bg-white rounded-xl shadow-md hover:shadow-lg transition-all p-8 text-center`,
            icon: `text-5xl mb-4`,
            itemTitle: `text-xl font-bold mb-4`,
            itemDesc: `text-base text-gray-500`,
            button: `inline-block rounded-[4px] px-[20px] py-[8px] text-[16px] font-[600] transition-all hover:scale-105 shadow-sm`
        };

        return comp;
    }

    enrichPricingSectionReact(comp, sec) {
        // Reuse universal for base styles
        comp = this.enrichUniversalReact(comp, sec);

        // Pricing specific enrichment
        if (comp.content.items) {
            comp.content.items = comp.content.items.map(item => {
                let features = [];
                if (item.desc) {
                    features = item.desc.split(/[✓\n•]/).map(f => f.trim()).filter(f => f.length > 0);
                }
                return {
                    ...item,
                    features: features.length > 0 ? features : (item.desc ? [item.desc] : []),
                    price: item.price || "$0",
                    buttonText: item.buttonText || "Get Started",
                    // OVERRIDE: Use captured item button style if available, else section default
                    buttonStyle: item.buttonStyle || comp.tailwind.buttonStyle || {}
                };
            });
        }
        return comp;
    }

    enrichTestimonialsReact(comp, sec) {
        // Reuse basic grid enrichment for base styles
        comp = this.enrichFeaturesGridReact(comp, sec);

        // Then add testimonial-specific item logic
        if (comp.content.items) {
            comp.content.items = comp.content.items.map(item => {
                return {
                    ...item,
                    quote: item.desc || "This product changed our business completely!",
                    role: item.role || "CEO, Company"
                };
            });
        }

        return comp;
    }

    enrichCTASectionReact(comp, sec) {
        const s = comp.styles;
        comp.content = {
            title: sec.title || "",
            description: sec.description || "",
            buttonText: sec.buttonText || "Get Started" // Fallback if scraping fails for 100% fidelity
        };

        const formatColor = (color, fallback) => {
            if (!color || color === 'transparent') return fallback;
            return color.startsWith('#') ? color : `#${color}`;
        };

        const bgColor = formatColor(s.backgroundColor, '#e8d5c4'); // Use beige default if missing
        const titleColor = formatColor(s.titleColor, '#2c3e50');
        const descColor = formatColor(s.descColor, 'rgba(44, 62, 80, 0.8)');
        const btnBg = formatColor(s.btnBg || s.btnColor, '#3b82f6');
        const btnTextColor = formatColor(s.btnTextColor, '#ffffff');

        comp.tailwind = {
            section: `w-full px-6`,
            sectionStyle: {
                backgroundColor: bgColor,
                backgroundImage: s.backgroundImage || 'none',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                paddingTop: s.paddingTop || '100px',
                paddingBottom: s.padding0Bottom || '100px',
                marginTop: s.marginTop || '0px',
                marginBottom: s.marginBottom || '0px'
            },
            inner: `max-w-4xl mx-auto text-center`,
            title: `text-4xl md:text-6xl font-black mb-8 leading-tight`,
            titleStyle: { color: titleColor },
            desc: `text-xl mb-12 opacity-90 mx-auto max-w-2xl`,
            descStyle: { color: descColor },
            button: `px-12 py-5 rounded-lg text-lg font-bold transition-all hover:opacity-90 active:scale-95 shadow-lg inline-block`,
            buttonStyle: {
                backgroundColor: btnBg,
                color: btnTextColor,
                borderRadius: s.btnRadius || '8px',
                padding: s.btnPadding || '16px 48px'
            }
        };
        return comp;
    }

    enrichBlogSectionReact(comp, sec) {
        // Use universal for base styles
        comp = this.enrichUniversalReact(comp, sec);

        // Ensure we have reasonable defaults for blog cards and map Date correctly
        if (comp.content.items) {
            comp.content.items = comp.content.items.map(item => ({
                ...item,
                date: item.date || item.role || 'Jan 15, 2024', // Use captured date or reliable default
                image: item.avatarSrc || item.image || null,
                desc: (item.desc && item.desc !== item.title) ? item.desc : '' // STRICT: Clean description
            }));
        }
        // Suppress section description for Blog to match Design
        comp.content.description = "";
        return comp;
    }

    enrichStackSectionReact(comp, sec) {
        // Use universal for base styles
        comp = this.enrichUniversalReact(comp, sec);

        // Ensure titles/descs are clean
        if (comp.content.items) {
            comp.content.items = comp.content.items.map(item => ({
                ...item,
                desc: (item.desc && item.desc !== item.title) ? item.desc : ''
            }));
        }

        // Stack specific: ensure grid is tight and clean
        comp.tailwind.grid = `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4`;
        return comp;
    }

    enrichGalleryReact(comp, sec) {
        const s = comp.styles;
        const variant = (sec.layoutVariant || 'layout-grid-3').toLowerCase();

        comp.content = {
            title: sec.title,
            description: sec.description || "",
            items: sec.items || []
        };

        // FORCE Responsive Grid for Gallery, ignore pixels
        let gridClass = `grid grid-cols-1 md:grid-cols-3 gap-4`;
        if (variant.includes('grid-2')) gridClass = `grid grid-cols-1 md:grid-cols-2 gap-4`;
        if (variant.includes('grid-4')) gridClass = `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`;
        if (variant === 'masonry') gridClass = `columns-1 md:columns-3 gap-4 space-y-4`;

        comp.tailwind = {
            section: `w-full py-20 px-6`,
            sectionStyle: {
                backgroundColor: s.backgroundColor || '#ffffff',
                backgroundImage: s.backgroundImage || 'none',
                backgroundSize: 'cover'
            },
            inner: `max-w-[1400px] mx-auto`,
            header: `text-${s.titleAlign || 'center'} mb-12`,
            title: `text-4xl font-bold mb-4`,
            titleStyle: { color: s.titleColor || '#2c3e50' },
            desc: `text-lg mb-8 max-w-4xl mx-auto`,
            descStyle: { color: s.descColor || '#5a6c7d' },

            grid: gridClass,
            // Ensure no conflicting inline styles
            gridStyle: { gap: s.gap },

            card: `overflow-hidden rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer group relative bg-gray-100`,
            cardStyle: {}, // No inline styles for card size
            image: `w-full h-64 object-cover transform group-hover:scale-110 transition-transform duration-500`, // Zoom effect on hover
            overlay: `absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100`,
            overlayText: `text-white font-bold text-lg drop-shadow-md`
        };

        return comp;
    }

    async exportReactTailwindZIP(page) {
        if (!window.JSZip) {
            alert('JSZip library not loaded.');
            return;
        }

        console.log("📦 Starting Strict React Export for:", page.name);

        const zip = new JSZip();
        const baseFolder = zip.folder("react-tailwind-export");
        const srcFolder = baseFolder.folder("src");
        const componentsFolder = srcFolder.folder("components");
        const sectionsFolder = srcFolder.folder("sections");
        const dataFolder = srcFolder.folder("data");

        // 1. Generate Page JSON
        const pageData = await this.generateReactTailwindFormat(page);
        dataFolder.file("page.json", JSON.stringify(pageData, null, 2));

        // Shared IconRenderer component
        componentsFolder.file("IconRenderer.jsx", `import React from 'react';
import * as Icons from 'lucide-react';

const IconRenderer = ({ name, className, style }) => {
  if (!name) return null;
  // Handle Emojis or short text - robust emoji detection with fallback regex
  let isEmoji = false;
  try {
    isEmoji = /\\p{Extended_Pictographic}/u.test(name) || name.length <= 2;
  } catch (e) {
    // Fallback for older environments
    isEmoji = name.length <= 2;
  }
  
  if (isEmoji || !/^[A-Z]/.test(name)) {
     return <span className={className} style={{ fontSize: '1.5em', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', ...style }}>{name}</span>;
  }
  const Icon = Icons[name] || Icons.Star || (() => null);
  return <Icon className={className || 'w-6 h-6'} style={style} />;
};
export default IconRenderer;`);

        // 2. Add Project Boilerplate (Tailwind v4 Compatible)
        baseFolder.file("package.json", JSON.stringify({
            name: "react-strict-wireframe",
            private: true,
            version: "0.1.0",
            type: "module",
            scripts: { "dev": "vite", "build": "vite build", "preview": "vite preview" },
            dependencies: { "react": "^18.3.0", "react-dom": "^18.3.0", "lucide-react": "^0.300.0" },
            devDependencies: {
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "@vitejs/plugin-react": "^4.3.0",
                "@tailwindcss/vite": "^4.0.0",
                "tailwindcss": "^4.0.0",
                "vite": "^6.0.0"
            }
        }, null, 2));

        baseFolder.file("vite.config.js", `import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()]
})`);

        // Tailwind v4 uses CSS-based configuration, no tailwind.config.js needed
        // The @import directives in index.css handle everything

        baseFolder.file("index.html", `<!doctype html><html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>${page.name}</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>`);
        baseFolder.file("README.md", "# React Export\nRun `npm install` and `npm run dev`.");

        // 3. Core React Files with Tailwind v4 CSS
        srcFolder.file("main.jsx", "import React from 'react';\nimport { createRoot } from 'react-dom/client';\nimport Home from './Home.jsx';\nimport './index.css';\nconst container = document.getElementById('root');\nif (container) {\n  const root = createRoot(container);\n  root.render(<React.StrictMode><Home /></React.StrictMode>);\n}");

        // Tailwind v4 CSS with proper imports
        srcFolder.file("index.css", `@import "tailwindcss";
@import "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap";

:root {
  --global-section-bg: ${getComputedStyle(document.documentElement).getPropertyValue('--global-section-bg').trim() || '#ffffff'};
  --wfe-text-color: ${getComputedStyle(document.documentElement).getPropertyValue('--wfe-text-color').trim() || '#1f2937'};
  --wfe-btn-bg: ${getComputedStyle(document.documentElement).getPropertyValue('--wfe-btn-bg').trim() || '#3b82f6'};
  --wfe-btn-text: ${getComputedStyle(document.documentElement).getPropertyValue('--wfe-btn-text').trim() || '#ffffff'};
}

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--global-section-bg);
  color: var(--wfe-text-color);
  margin: 0;
}`);

        // Generate Home.jsx with all specialized components import and cases
        srcFolder.file("Home.jsx", `import React, { useEffect, useState } from 'react';
import pageData from './data/page.json';
import Navbar from './sections/Navbar.jsx';
import Footer from './sections/Footer.jsx';
import HeroSection from './sections/HeroSection.jsx';
import FeaturesGrid from './sections/FeaturesGrid.jsx';
import FeaturesList from './sections/FeaturesList.jsx';
import PricingSection from './sections/PricingSection.jsx';
import Testimonials from './sections/Testimonials.jsx';
import BlogSection from './sections/BlogSection.jsx';
import GallerySection from './sections/GallerySection.jsx';
import CTASection from './sections/CTASection.jsx';
import StackSection from './sections/StackSection.jsx';
import StatsSection from './sections/StatsSection.jsx';
import MapSection from './sections/MapSection.jsx';
import ContactSection from './sections/ContactSection.jsx';
import AboutSection from './sections/AboutSection.jsx';
import ImageTextSection from './sections/ImageTextSection.jsx';
import ServicesGrid from './sections/ServicesGrid.jsx';
import ProductGrid from './sections/ProductGrid.jsx';
import TeamSection from './sections/TeamSection.jsx';
import FAQSection from './sections/FAQSection.jsx';
import ProcessSection from './sections/ProcessSection.jsx';
import SidebarSection from './sections/SidebarSection.jsx';
import Section from './sections/Section.jsx';

const SectionRenderer = ({ section }) => {
  switch (section.type) {
    case 'Navbar': return <Navbar data={section} />;
    case 'HeroSection': return <HeroSection data={section} />;
    case 'FeaturesGrid': return <FeaturesGrid data={section} />;
    case 'FeaturesList': return <FeaturesList data={section} />;
    case 'PricingSection': return <PricingSection data={section} />;
    case 'Testimonials': return <Testimonials data={section} />;
    case 'BlogSection': return <BlogSection data={section} />;
    case 'GallerySection': return <GallerySection data={section} />;
    case 'CTASection': return <CTASection data={section} />;
    case 'StackSection': return <StackSection data={section} />;
    case 'StatsSection': return <StatsSection data={section} />;
    case 'MapSection': return <MapSection data={section} />;
    case 'ContactSection': return <ContactSection data={section} />;
    case 'AboutSection': return <AboutSection data={section} />;
    case 'ImageTextSection': return <ImageTextSection data={section} />;
    case 'ServicesGrid': return <ServicesGrid data={section} />;
    case 'ProductGrid': return <ProductGrid data={section} />;
    case 'TeamSection': return <TeamSection data={section} />;
    case 'FAQSection': return <FAQSection data={section} />;
    case 'ProcessSection': return <ProcessSection data={section} />;
    case 'SidebarSection': return <SidebarSection data={section} />;
    case 'Footer': return <Footer data={section} />;
    default: return <Section data={section} />;
  }
};

const Home = () => {
  const { page } = pageData;
  return (
    <main className="min-h-screen w-full">
        {page.sections.map((section, index) => (
          <SectionRenderer key={section.id || index} section={section} />
        ))}
    </main>
  );
};
export default Home;`);

        // 4. Component Templates (Using the Strict Tailwind Props)

        // Navbar
        sectionsFolder.file("Navbar.jsx", `import React from 'react';
const Navbar = ({ data }) => {
  const { content, tailwind = {}, styles = {} } = data;
  const isCenteredLogo = (tailwind.inner || '').includes('grid-cols-3');

  return (
    <nav className={tailwind.nav || ''} style={tailwind.navStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto flex justify-between items-center'}>
        {isCenteredLogo ? (
          <>
            <div className="flex gap-6 justify-end items-center">
              {(content.splitLinks?.left || []).map((link, i) => (
                <a key={i} href="#" className={tailwind.link || ''} style={tailwind.linkStyle || {}}>{link}</a>
              ))}
            </div>
            <div className={tailwind.logo || 'font-bold'} style={tailwind.logoStyle || {}}>{content.logo}</div>
            <div className="flex gap-6 justify-between items-center">
              <div className="flex gap-6 items-center">
                {(content.splitLinks?.right || []).map((link, i) => (
                  <a key={i} href="#" className={tailwind.link || ''} style={tailwind.linkStyle || {}}>{link}</a>
                ))}
              </div>
              {content.cta && (
                <button className={tailwind.button || ''} style={tailwind.buttonStyle || {}}>{content.cta}</button>
              )}
            </div>
          </>
        ) : (
          <>
            <div className={tailwind.logo || 'font-bold'} style={tailwind.logoStyle || {}}>{content.logo}</div>
            <div className={tailwind.links || 'flex gap-8'}>
              {(content.links || []).map((link, i) => (
                <a key={i} href="#" className={tailwind.link || ''} style={tailwind.linkStyle || {}}>{link}</a>
              ))}
              {content.cta && (
                <button className={tailwind.button || ''} style={tailwind.buttonStyle || {}}>{content.cta}</button>
              )}
            </div>
          </>
        )}
      </div>
    </nav>
  );
};
export default Navbar;`);

        // Hero
        sectionsFolder.file("HeroSection.jsx", `import React from 'react';
const HeroSection = ({ data }) => {
  const { content, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        <div className={tailwind.textWrapper || 'flex flex-col'}>
          {content.heading && <h1 className={tailwind.heading || 'text-4xl font-bold'} style={tailwind.headingStyle || {}}>{content.heading}</h1>}
          {content.subtext && <p className={tailwind.subtext || 'mt-4'} style={tailwind.subtextStyle || {}}>{content.subtext}</p>}
          {content.cta && (
            <div className="flex flex-col sm:flex-row gap-4 mt-8">
              <button className={tailwind.button || ''} style={tailwind.buttonStyle || {}}>{content.cta}</button>
            </div>
          )}
        </div>
        <div className={tailwind.mockupContainer || 'mt-12'}>
           <div className={tailwind.mockup || ''} style={tailwind.mockupStyle || {}}>
              {content.image ? (
                <img src={content.image} alt={content.heading} className="w-full h-full object-cover rounded-lg" />
              ) : (
                <div className="w-full h-full bg-white/50 backdrop-blur-sm rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300 text-gray-400 font-medium min-h-[300px]">
                    Hero Mockup
                </div>
              )}
           </div>
        </div>
      </div>
    </section>
  );
};
export default HeroSection;`);

        // CTA Section
        sectionsFolder.file("CTASection.jsx", `import React from 'react';
const CTASection = ({ data }) => {
  const { content, tailwind } = data;
  return (
    <section className={tailwind.section} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner}>
        <h2 className={tailwind.title} style={tailwind.titleStyle || {}}>{content.title}</h2>
        {content.description && <p className={tailwind.desc} style={tailwind.descStyle || {}}>{content.description}</p>}
        {content.buttonText && (
          <button className={tailwind.button} style={tailwind.buttonStyle || {}}>
            {content.buttonText}
          </button>
        )}
      </div>
    </section>
  );
};
export default CTASection;`);

        // Stack Section
        sectionsFolder.file("StackSection.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';
const StackSection = ({ data }) => {
  const { content, tailwind } = data;
  return (
    <section className={tailwind.section} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner}>
        <div className={tailwind.header}>
            <h2 className={tailwind.title} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        <div className={tailwind.grid} style={tailwind.gridStyle || {}}>
           {(content.items || []).map((item, i) => (
             <div key={i} className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 bg-white/50 backdrop-blur-sm shadow-sm transition-all hover:shadow-md hover:bg-white" style={item.cardStyle || {}}>
                <div className="w-12 h-12 flex items-center justify-center bg-gray-50 rounded-lg shrink-0">
                   <IconRenderer name={item.icon} className="w-6 h-6" />
                </div>
                <div>
                   <h3 className="font-bold text-gray-900" style={item.titleStyle || {}}>{item.title}</h3>
                   {item.desc && <p className="text-sm text-gray-500 line-clamp-1" style={item.descStyle || {}}>{item.desc}</p>}
                </div>
             </div>
           ))}
        </div>
      </div>
    </section>
  );
};
export default StackSection;`);

        // Stats Section
        sectionsFolder.file("StatsSection.jsx", `import React from 'react';
const StatsSection = ({ data }) => {
  const { content, tailwind } = data;
  return (
    <section className={tailwind.section} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner}>
        <div className={tailwind.header}>
            <h2 className={tailwind.title} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        <div className={tailwind.grid} style={tailwind.gridStyle || {}}>
          {(content.items || []).map((item, i) => (
            <div key={i} className="text-center p-6" style={item.cardStyle || {}}>
               <h3 className={tailwind.itemTitle} style={item.titleStyle || tailwind.itemTitleStyle || {}}>{item.title}</h3>
               <p className={tailwind.itemDesc} style={item.descStyle || tailwind.itemDescStyle || {}}>{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default StatsSection;`);

        // Features Grid (2x2)
        sectionsFolder.file("FeaturesGrid.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';

const FeaturesGrid = ({ data }) => {
  const { content, tailwind = {} } = data;
  const items = content.items || [];
  
  // High Fidelity Paragraph Parsing
  const description = content.description || "";
  const paragraphs = description.split(/\\n\\s*\\n/).filter(p => p.trim().length > 0);

  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        <div className={tailwind.header || 'text-center mb-12'}>
            <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {description && (
              <div className={(tailwind.desc || '') + " space-y-6"} style={tailwind.descStyle || {}}>
                {paragraphs.length > 1 ? (
                  paragraphs.map((p, i) => (
                    <p key={i} className="whitespace-pre-line leading-relaxed">{p.trim()}</p>
                  ))
                ) : (
                  <p className="whitespace-pre-line leading-relaxed">{description}</p>
                )}
              </div>
            )}
        </div>
        
        <div className={tailwind.grid || 'grid grid-cols-1 md:grid-cols-3 gap-8'} style={tailwind.gridStyle || {}}>
          {items.map((item, i) => {
            const cs = item.cardStyle || {};
            const isRow = cs.flexDirection === 'row';
            const cardLayout = isRow ? 'flex flex-row items-start' : 'flex flex-col items-start';
            const mergedCardStyle = {...(tailwind.cardStyle || {}), ...cs};
            const cardAlign = cs.textAlign || tailwind.card?.match(/text-(start|center|end)/)?.[1] || 'center';
            
            return (
            <div key={i} className={(tailwind.card || '') + ' ' + cardLayout + ' text-' + cardAlign} style={mergedCardStyle}>
                {(item.avatarSrc || item.icon) && (
                  <div className={"flex-shrink-0 " + (cardAlign === 'center' ? 'mx-auto' : '')} style={item.iconStyle || {}}>
                     {item.avatarSrc ? (
                         <img src={item.avatarSrc} alt={item.title} className="w-full h-full object-cover rounded-lg" />
                     ) : (
                         <IconRenderer name={item.icon} className="" style={{ fontSize: (item.iconStyle && item.iconStyle.fontSize) || '2rem' }} />
                     )}
                  </div>
                )}
               <div className={isRow ? 'flex flex-col flex-1 gap-1' : (cardAlign === 'center' ? 'w-full' : '')}>
                 <h3 className={tailwind.itemTitle || 'font-bold'} style={{...(tailwind.itemTitleStyle || {}), ...(item.titleStyle || {})}}>{item.title}</h3>
                 <p className={tailwind.itemDesc || ''} style={{...(tailwind.itemDescStyle || {}), ...(item.descStyle || {})}}>{item.desc}</p>
               </div>
            </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
export default FeaturesGrid;`);

        // Features List (Horizontal)
        sectionsFolder.file("FeaturesList.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';

const FeaturesList = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  const isCarousel = (tailwind.list || '').includes('overflow-x-auto');

  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        <div className={tailwind.header || 'text-center mb-12'}>
            <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc || 'mt-4'} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        
        <div className={tailwind.list || tailwind.grid || 'flex flex-col gap-6'} style={tailwind.listStyle || tailwind.gridStyle || {}}>
          {(content.items || []).map((item, i) => {
            const cs = item.cardStyle || {};
            const mergedCardStyle = {...(tailwind.cardStyle || {}), ...cs};
            return (
            <div key={i} className={tailwind.card || ''} style={mergedCardStyle}>
               <div className="flex-shrink-0">
                   {(item.avatarSrc || item.icon) && (
                     <div className={tailwind.iconWrapper || 'flex items-center justify-center'} style={item.iconStyle || {}}>
                        {item.avatarSrc ? (
                            <img src={item.avatarSrc} alt={item.title} className="w-full h-full object-cover rounded-lg" />
                        ) : (
                            <IconRenderer name={item.icon} className="" style={{ fontSize: (item.iconStyle && item.iconStyle.fontSize) || '2rem' }} />
                        )}
                     </div>
                   )}
               </div>
               <div className={tailwind.itemContent || 'flex flex-col flex-1 gap-1'}>
                 <h3 className={tailwind.itemTitle || 'font-bold'} style={{...(tailwind.itemTitleStyle || {}), ...(item.titleStyle || {})}}>{item.title}</h3>
                 <p className={tailwind.itemDesc || ''} style={{...(tailwind.itemDescStyle || {}), ...(item.descStyle || {})}}>{item.desc}</p>
               </div>
            </div>
            );
          })}
        </div>

        {isCarousel && (
          <div className="flex justify-center gap-2 mt-8 text-gray-400">
            <span className="cursor-pointer hover:text-gray-600">◀</span>
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <span className="w-2 h-2 rounded-full bg-gray-300"></span>
            <span className="w-2 h-2 rounded-full bg-gray-300"></span>
            <span className="cursor-pointer hover:text-gray-600">▶</span>
          </div>
        )}
      </div>
    </section>
  );
};
export default FeaturesList;`);

        // Pricing Section
        sectionsFolder.file("PricingSection.jsx", `import React from 'react';
const PricingSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        <div className={tailwind.header || 'text-center mb-12'}>
            <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc || 'mt-4'} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        <div className={tailwind.grid || 'grid grid-cols-1 md:grid-cols-3 gap-8'} style={tailwind.gridStyle || {}}>
          {(content.items || []).map((item, i) => (
            <div key={i} className={tailwind.card || ''} style={{...(tailwind.cardStyle || {}), ...(item.cardStyle || {}), position: 'relative'}}>
               {item.isPopular && (
                 <div className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full absolute -top-3 left-1/2 -translate-x-1/2 uppercase tracking-wide z-10">
                    Popular
                 </div>
               )}
               <h3 className={tailwind.itemTitle || "text-xl font-bold mb-4"} style={{...(tailwind.itemTitleStyle || {}), ...(item.titleStyle || {})}}>{item.title}</h3>
               <div className="flex items-baseline gap-1 my-4">
                  <span className="text-4xl font-bold" style={item.priceStyle || {}}>{item.price}</span>
                  <span className="text-gray-500">/mo</span>
               </div>
               <div className="flex flex-col gap-3 mb-8 w-full">
                  {(item.features || []).map((feat, j) => (
                    <div key={j} className="flex items-center gap-2 text-sm opacity-80" style={{color: (item.descStyle && item.descStyle.color) || 'inherit'}}>
                       <span className="text-green-500">✓</span>
                       <span>{feat}</span>
                    </div>
                  ))}
               </div>
               <button className={tailwind.button || ''} style={item.buttonStyle || tailwind.buttonStyle || {}}>
                 {item.buttonText}
               </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default PricingSection;`);

        // Testimonials Template (Matches Wireframe High-Fidelity)
        sectionsFolder.file("Testimonials.jsx", `import React from 'react';
const Testimonials = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        <div className={tailwind.header || 'text-center mb-12'}>
            <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc || 'mt-4'} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>

        <div className={tailwind.grid || 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8'}>
            {(content.items || []).map((item, i) => (
              <div key={i} className={tailwind.card || ''} style={item.cardStyle || tailwind.cardStyle || {}}>
                 <div className="text-blue-500 text-3xl mb-4 italic opacity-50 font-serif">"</div>
                 <p className="text-gray-600 italic mb-6 leading-relaxed" style={item.descStyle || {}}>
                   {item.quote || item.desc}
                 </p>
                 <div className="flex items-center gap-4 mt-auto">
                    <div className="w-12 h-12 rounded-full bg-gray-200 flex-shrink-0 flex items-center justify-center overflow-hidden">
                       {item.avatarSrc ? <img src={item.avatarSrc} className="w-full h-full object-cover" alt="" /> : <div className="text-gray-400">👤</div>}
                    </div>
                    <div>
                       <h4 className="font-bold text-gray-900 leading-tight" style={item.titleStyle || {}}>{item.title}</h4>
                       {item.role && <p className="text-sm text-gray-500">{item.role}</p>}
                    </div>
                 </div>
              </div>
            ))}
        </div>
      </div>
    </section>
  );
};
export default Testimonials;`);

        // Blog Section Template (Fixed Grid)
        sectionsFolder.file("BlogSection.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';
const BlogSection = ({ data }) => {
  const { content, tailwind } = data;
  return (
    <section className={tailwind.section} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner}>
        <div className={tailwind.header}>
            <h2 className={tailwind.title} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        
        {/* Force Grid Layout for Blog */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {(content.items || []).map((item, i) => (
            <div key={i} className={tailwind.card} style={{...(tailwind.cardStyle || {}), ...(item.cardStyle || {})}}>
               {item.image ? (
                 <img src={item.image} alt={item.title} className="h-48 w-full object-cover rounded-t-xl mb-4" />
               ) : (
                 <div className="h-48 rounded-t-xl mb-4 flex items-center justify-center opacity-20" style={{ backgroundColor: (item.iconStyle && item.iconStyle.backgroundColor) || 'rgba(0,0,0,0.05)' }}>
                    <IconRenderer name="Image" className="w-8 h-8" />
                 </div>
               )}
               <div className="p-4">
                 <div className="text-xs opacity-50 mb-2" style={{color: (item.descStyle && item.descStyle.color) || 'inherit'}}>{item.date || 'Jan 15, 2024'}</div>
                 <h3 className={tailwind.itemTitle || "text-xl font-bold mb-2"} style={{...(tailwind.itemTitleStyle || {}), ...(item.titleStyle || {})}}>{item.title}</h3>
                 {item.desc && <p className={tailwind.itemDesc || "text-base mt-2"} style={{...(tailwind.itemDescStyle || {}), ...(item.descStyle || {})}}>{item.desc}</p>}
                 <div className="mt-4 text-blue-600 text-sm font-semibold cursor-pointer hover:underline">Read More →</div>
               </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default BlogSection;`);

        // Gallery Section Template
        sectionsFolder.file("GallerySection.jsx", `import React, { useState } from 'react';
const GallerySection = ({ data }) => {
  const { content, tailwind } = data;
  const [selectedImage, setSelectedImage] = useState(null);

  return (
    <section className={tailwind.section} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner}>
        <div className={tailwind.header}>
            <h2 className={tailwind.title} style={tailwind.titleStyle || {}}>{content.title}</h2>
            {content.description && <p className={tailwind.desc} style={tailwind.descStyle || {}}>{content.description}</p>}
        </div>
        
        <div className={tailwind.grid}>
          {(content.items || []).map((item, i) => (
            <div key={i} className={tailwind.card} onClick={() => setSelectedImage(item.image || item.avatarSrc)}>
               <img 
                 src={item.image || item.avatarSrc || 'https://via.placeholder.com/400'} 
                 alt={item.title} 
                 className={tailwind.image} 
               />
               <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                 <div className="text-center">
                    <h3 className="text-white font-bold text-xl">{item.title}</h3>
                    <p className="text-white/80 text-sm">View Details</p>
                 </div>
               </div>
            </div>
          ))}
        </div>

        {/* Lightbox Modal */}
        {selectedImage && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" onClick={() => setSelectedImage(null)}>
            <img src={selectedImage} alt="Full view" className="max-w-full max-h-[90vh] object-contain rounded-md shadow-2xl" />
          </div>
        )}
      </div>
    </section>
  );
};
export default GallerySection;`);
        // Map Section Template
        sectionsFolder.file("MapSection.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';

const MapSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  
  const description = content.address || "";
  const paragraphs = description.split(/\\n/).filter(p => p.trim().length > 0);

  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        {/* Optional Secondary Title (at the top) */}
        {/* <div className="mb-8">
            <h2 className="text-xl font-bold opacity-60">Our Location</h2>
        </div> */}

        {/* Map Mockup Container - Widescreen */}
        <div className={tailwind.mockupWrapper || 'w-full mb-12 aspect-video'} style={tailwind.mockupStyle || {}}>
            <div className="w-full h-full flex flex-col items-center justify-center shadow-inner overflow-hidden relative">
                <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                <IconRenderer name={content.mockup.icon} className="text-6xl text-blue-400 mb-4 z-10" />
                <span className="text-xl font-medium text-blue-500 z-10">{content.mockup.label}</span>
            </div>
        </div>

        {/* Contact info below map - Centered */}
        <div className={tailwind.header || 'text-center'}>
             <h3 className={tailwind.title || 'text-2xl font-bold mb-4'} style={tailwind.titleStyle || {}}>{content.title}</h3>
            {description && (
              <div className={tailwind.desc || 'space-y-2'} style={tailwind.descStyle || {}}>
                {paragraphs.map((p, i) => (
                    <p key={i} className="whitespace-pre-line leading-relaxed opacity-90">{p.trim()}</p>
                ))}
              </div>
            )}
        </div>
      </div>
    </section>
  );
};
export default MapSection;`);

        // Contact Section Template
        sectionsFolder.file("ContactSection.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';

const ContactSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  const s = data.styles || {};

  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        {/* Contact Form Header */}
        <div className="mb-12">
            <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>{content.title}</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-start">
            {/* Form Column */}
            <div className="space-y-6">
                {(content.form.fields || []).map((field, i) => (
                    <div key={i} className="flex flex-col gap-2">
                        <label className="text-sm font-semibold opacity-70">{field.label}</label>
                        {field.type === 'textarea' ? (
                            <textarea 
                                placeholder={field.placeholder}
                                className="w-full p-4 rounded-xl bg-white border border-black/5 min-h-[150px] outline-none focus:border-blue-500 transition-all shadow-sm"
                            />
                        ) : (
                            <input 
                                type={field.type}
                                placeholder={field.placeholder}
                                className="w-full p-4 rounded-xl bg-white border border-black/5 outline-none focus:border-blue-500 transition-all shadow-sm"
                            />
                        )}
                    </div>
                ))}
                <button 
                    className="w-full py-4 rounded-xl font-bold transition-all hover:opacity-90 active:scale-[0.98] shadow-md"
                    style={{ backgroundColor: s.btnBg || '#3b82f6', color: s.btnTextColor || '#fff' }}
                >
                    {content.form.button}
                </button>
            </div>

            {/* Sidebar Column */}
            <div className="space-y-12">
                <div className="grid grid-cols-1 gap-8">
                    {(content.sidebar.items || []).map((item, i) => (
                        <div key={i} className="flex items-start gap-4">
                            <div className="text-3xl mt-1 opacity-100 flex-shrink-0"><IconRenderer name={item.icon} /></div>
                            <div>
                                <h3 className="font-bold text-lg mb-1">{item.title}</h3>
                                <p className="opacity-80 whitespace-pre-line leading-relaxed">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Map Mockup */}
                <div className="bg-blue-50/50 rounded-3xl border border-blue-100 flex flex-col items-center justify-center p-12 min-h-[300px] shadow-inner">
                    <IconRenderer name={content.sidebar.mockup.icon} className="text-5xl text-blue-300 mb-4" />
                    <span className="text-lg font-medium text-blue-400">{content.sidebar.mockup.label}</span>
                </div>
            </div>
        </div>
      </div>
    </section>
  );
};
export default ContactSection;`);

        // Footer Template (Matches Wireframe High-Fidelity)
        sectionsFolder.file("Footer.jsx", `import React from 'react';
const Footer = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <footer className={tailwind.footer || ''} style={tailwind.footerStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        {/* Footer Top Title and Line */}
        <div className="mb-8">
           <h2 className={tailwind.brand || "text-xl font-bold mb-4"} style={tailwind.brandStyle || {}}>{content.brand}</h2>
           <hr className="border-gray-200/50" />
        </div>

        {/* 4-Column Grid */}
        <div className={tailwind.grid}>
            {(content.columns || []).map((col, i) => (
              <div key={i}>
                 <h3 className={tailwind.colTitle} style={tailwind.colTitleStyle || {}}>{col.title}</h3>
                 <ul className="space-y-3">
                   {(col.links || []).map((link, j) => (
                      <li key={j}><a href="#" className={tailwind.link} style={tailwind.linkStyle || {}}>{link}</a></li>
                   ))}
                 </ul>
              </div>
            ))}
        </div>

        {/* Footer Bottom Line and Copyright */}
        <div className="mt-12">
          <div className={tailwind.copyright} style={tailwind.copyrightStyle || {}}>
            {content.copyright}
          </div>
        </div>
      </div>
    </footer>
  );
};
export default Footer;`);

        // Universal Section Component (handles ANY section type dynamically)
        sectionsFolder.file("Section.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';

const Section = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  const layout = tailwind.layout || { type: 'block' };
  
  return (
    <section className={tailwind.section || ''} style={tailwind.sectionStyle || {}}>
      <div className={tailwind.inner || 'max-w-7xl mx-auto'}>
        {/* Header */}
        {(content.title || content.description) && (
          <div className={tailwind.header || 'text-center mb-12'}>
            {content.title && (
              <h2 className={tailwind.title || 'text-3xl font-bold'} style={tailwind.titleStyle || {}}>
                {content.title}
              </h2>
            )}
            {content.description && (
              <p className={tailwind.desc || 'mt-4'} style={tailwind.descStyle || {}}>
                {content.description}
              </p>
            )}
          </div>
        )}
        
        {/* Items Container - Dynamic based on layout */}
        {content.items && content.items.length > 0 && (
          <div 
            className={tailwind.itemsContainer || tailwind.grid || tailwind.list || 'grid grid-cols-1 md:grid-cols-3 gap-8'} 
            style={tailwind.itemsContainerStyle || {}}
          >
            {content.items.map((item, i) => (
              <div key={i} className={tailwind.card || ''} style={tailwind.cardStyle || {}}>
                {/* Icon or Image */}
                {(item.icon || item.avatarSrc) && (
                  <div className={tailwind.iconWrapper || ''} style={item.iconStyle || tailwind.iconStyle || {}}>
                    {item.avatarSrc ? (
                      <img src={item.avatarSrc} alt={item.title} className="w-full h-full object-cover rounded-full" />
                    ) : (
                      <IconRenderer name={item.icon} className="w-[1em] h-[1em]" />
                    )}
                  </div>
                )}
                
                
                {/* Title */}
                {item.title && (
                  <h3 
                    className={tailwind.itemTitle || 'font-bold'} 
                    style={item.titleStyle || tailwind.itemTitleStyle || {}}
                  >
                    {item.title}
                  </h3>
                )}
                
                {/* Description */}
                {item.desc && (
                  <p 
                    className={tailwind.itemDesc || ''} 
                    style={item.descStyle || tailwind.itemDescStyle || {}}
                  >
                    {item.desc}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
        
        {/* Button */}
        {content.buttonText && (
          <div className="mt-8 flex justify-center">
            <button className={tailwind.button || ''} style={tailwind.buttonStyle || {}}>
              {content.buttonText}
            </button>
          </div>
        )}
      </div>
    </section>
  );
};
export default Section;`);

        // About Section
        sectionsFolder.file("AboutSection.jsx", `import React from 'react';
const AboutSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div>
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">About Us</span>
          <h2 className="text-3xl font-bold mb-4">{content.title || 'About Our Mission'}</h2>
          <p className="text-base text-gray-600 leading-relaxed mb-6">{content.description}</p>
          {content.items && content.items.length > 0 && (
            <div className="flex gap-8 pt-6 border-t border-gray-100">
              {content.items.slice(0, 3).map((item, i) => (
                <div key={i}>
                  <div className="text-3xl font-bold text-blue-600">{item.title || item.value}</div>
                  <div className="text-sm text-gray-500 mt-1">{item.desc || item.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="w-full h-80 rounded-2xl bg-gray-100 border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-400 font-semibold">
          Brand Story Visual
        </div>
      </div>
    </section>
  );
};
export default AboutSection;`);

        // Image Text Section
        sectionsFolder.file("ImageTextSection.jsx", `import React from 'react';
const ImageTextSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div className="w-full h-80 rounded-2xl bg-gray-100 border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-400 font-semibold">
          Architecture Showcase
        </div>
        <div>
          <h2 className="text-3xl font-bold mb-4">{content.title || 'Transforming Concepts into Execution'}</h2>
          <p className="text-base text-gray-600 leading-relaxed mb-6">{content.description}</p>
          {content.items && (
            <ul className="space-y-3">
              {content.items.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-green-500 font-bold">✓</span>
                  <span><strong>{item.title}:</strong> {item.desc}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
};
export default ImageTextSection;`);

        // Services Grid
        sectionsFolder.file("ServicesGrid.jsx", `import React from 'react';
import IconRenderer from '../components/IconRenderer';
const ServicesGrid = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">What We Offer</span>
          <h2 className="text-3xl font-bold mb-3">{content.title || 'Our Services'}</h2>
          <p className="text-gray-600">{content.description}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {(content.items || []).map((item, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-xl p-8 flex flex-col items-start shadow-sm hover:shadow-md transition-all">
              <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-2xl mb-5">
                <IconRenderer name={item.icon || 'Briefcase'} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{item.title}</h3>
              <p className="text-gray-600 text-sm flex-1 leading-relaxed">{item.desc}</p>
              {item.price && <div className="text-blue-600 font-bold text-sm mt-4">{item.price}</div>}
              <button className="mt-4 text-sm font-semibold text-blue-600 hover:underline">Learn More →</button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default ServicesGrid;`);

        // Product Grid
        sectionsFolder.file("ProductGrid.jsx", `import React from 'react';
const ProductGrid = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">Store Catalog</span>
          <h2 className="text-3xl font-bold mb-3">{content.title || 'Featured Products'}</h2>
          <p className="text-gray-600">{content.description}</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {(content.items || []).map((item, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-xl overflow-hidden flex flex-col shadow-sm hover:shadow-md transition-all">
              <div className="h-44 bg-gray-100 border-b border-dashed border-gray-200 flex items-center justify-center text-gray-400 font-medium">
                {item.title || 'Product Photo'}
              </div>
              <div className="p-4 flex flex-col flex-1">
                <div className="text-amber-500 text-xs mb-1">★★★★★</div>
                <h4 className="font-semibold text-gray-900 text-sm mb-3">{item.title || 'Product'}</h4>
                <div className="flex justify-between items-center mt-auto">
                  <span className="font-bold text-lg text-gray-900">{item.price || '$99'}</span>
                  <button className="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors">Add to Cart</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default ProductGrid;`);

        // Team Section
        sectionsFolder.file("TeamSection.jsx", `import React from 'react';
const TeamSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">Leadership</span>
          <h2 className="text-3xl font-bold mb-3">{content.title || 'Meet the Team'}</h2>
          <p className="text-gray-600">{content.description}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {(content.items || []).map((member, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-xl p-6 text-center shadow-sm">
              <div className="w-24 h-24 rounded-full bg-gray-200 border-2 border-dashed border-gray-300 mx-auto mb-4 flex items-center justify-center text-gray-400 text-2xl font-bold">
                {(member.name || member.title || 'U')[0]}
              </div>
              <h3 className="font-bold text-gray-900 text-lg">{member.name || member.title}</h3>
              <div className="text-blue-600 text-sm font-semibold mb-2">{member.role || 'Team Lead'}</div>
              <p className="text-gray-500 text-sm leading-relaxed mb-4">{member.desc}</p>
              <div className="text-xs text-gray-400 font-medium">LinkedIn • Twitter</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default TeamSection;`);

        // FAQ Section
        sectionsFolder.file("FAQSection.jsx", `import React, { useState } from 'react';
const FAQSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  const [openIndex, setOpenIndex] = useState(0);
  const items = content.items || [];
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">Got Questions?</span>
          <h2 className="text-3xl font-bold mb-3">{content.title || 'Frequently Asked Questions'}</h2>
          <p className="text-gray-600">{content.description}</p>
        </div>
        <div className="space-y-3">
          {items.map((item, i) => {
            const isOpen = openIndex === i;
            return (
              <div key={i} className="bg-white border border-gray-200 rounded-xl overflow-hidden transition-all shadow-sm">
                <button
                  className="w-full px-6 py-4 text-left font-semibold text-gray-900 flex justify-between items-center hover:bg-gray-50"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                >
                  <span>{item.title || item.question}</span>
                  <span className={'transform transition-transform ' + (isOpen ? 'rotate-180' : '')}>▾</span>
                </button>
                {isOpen && (
                  <div className="px-6 pb-4 text-gray-600 text-sm leading-relaxed border-t border-gray-100 pt-3">
                    {item.desc || item.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
export default FAQSection;`);

        // Process Section
        sectionsFolder.file("ProcessSection.jsx", `import React from 'react';
const ProcessSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 uppercase tracking-wide mb-3">The Workflow</span>
          <h2 className="text-3xl font-bold mb-3">{content.title || 'How It Works'}</h2>
          <p className="text-gray-600">{content.description}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {(content.items || []).map((step, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-xl p-6 text-center shadow-sm">
              <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-extrabold flex items-center justify-center mx-auto mb-4">
                {i + 1}
              </div>
              <h3 className="font-bold text-gray-900 text-base mb-2">{step.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
export default ProcessSection;`);

        // Sidebar Section
        sectionsFolder.file("SidebarSection.jsx", `import React from 'react';
const SidebarSection = ({ data }) => {
  const { content = {}, tailwind = {} } = data;
  return (
    <section className={tailwind.section || 'w-full py-20 px-6'} style={tailwind.sectionStyle || {}}>
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-3xl font-bold text-gray-900">{content.title || 'Editorial Hub'}</h2>
          <p className="text-gray-600 leading-relaxed text-base">{content.description}</p>
          <div className="w-full h-72 rounded-2xl bg-gray-100 border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-400 font-semibold">
            Featured Content Visual
          </div>
        </div>
        <aside className="space-y-6">
          <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm">
            <h4 className="font-bold text-gray-900 mb-3 text-base">Quick Search</h4>
            <input type="text" placeholder="Search documentation..." className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" readOnly />
          </div>
          <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm">
            <h4 className="font-bold text-gray-900 mb-3 text-base">Key Categories</h4>
            <ul className="space-y-2 text-sm text-blue-600">
              <li>Architecture Overview (12)</li>
              <li>Component Catalog (32)</li>
              <li>AI Providers (4)</li>
            </ul>
          </div>
        </aside>
      </div>
    </section>
  );
};
export default SidebarSection;`);


        // 5. Generate and Download
        zip.generateAsync({ type: "blob" }).then(function (content) {
            const link = document.createElement("a");
            link.href = URL.createObjectURL(content);
            link.download = `${(page.name || "page").toLowerCase().replace(/\s+/g, "-")}-react-strict.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            console.log("✅ React Strict Export Downloaded");
        });
    }

    // --- GENERIC EXPORT (Keeping HTML/CSS as is) ---


    async generateHTMLCSSFormat(page) {
        console.log("🎨 Generating Full-Width HTML/CSS Export for:", page.name);

        const pageColumn = document.querySelector(`.wireframe-page-column[data-page-id="${page.id}"]`);
        if (!pageColumn) {
            console.error("❌ Could not find page in DOM for export");
            return "<html><body><h1>Error: Page not found in editor. Please ensure it is rendered.</h1></body></html>";
        }

        // Fetch External CSS
        let externalCSS = '';
        try {
            console.log("📥 Fetching external stylesheets...");
            const [wireframeCSS, styleCSS] = await Promise.all([
                fetch('css/wireframe.css').then(res => {
                    if (!res.ok) throw new Error(`Failed to load wireframe.css: ${res.statusText}`);
                    return res.text();
                }),
                fetch('css/style.css').then(res => {
                    if (!res.ok) throw new Error(`Failed to load style.css: ${res.statusText}`);
                    return res.text();
                })
            ]);

            externalCSS = `
            /* --- css/wireframe.css --- */
            ${wireframeCSS}
            
            /* --- css/style.css --- */
            ${styleCSS}
            `;
            console.log("✅ External CSS fetched successfully.");
        } catch (e) {
            console.warn("⚠️ Could not fetch external CSS for export, falling back to minimal styles:", e);
        }

        const rootStyles = getComputedStyle(document.documentElement);
        const contentClone = pageColumn.querySelector('.page-column-content').cloneNode(true);
        contentClone.querySelectorAll('.section-toolbar, .delete-btn, .section-label, .toolbar-btn').forEach(el => el.remove());
        contentClone.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));

        const globalVars = [
            '--global-section-bg',
            '--wfe-text-color',
            '--wfe-btn-bg',
            '--wfe-btn-text',
            '--wfe-font-heading',
            '--wfe-font-body',
            '--wfe-section-padding',
            '--wfe-section-margin'
        ];

        let rootVarsCSS = ':root {\n';
        globalVars.forEach(v => {
            const val = rootStyles.getPropertyValue(v).trim();
            if (val) rootVarsCSS += `    ${v}: ${val};\n`;
        });
        rootVarsCSS += '}';

        const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${page.name || 'Exported Page'}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&family=Abril+Fatface&family=Playfair+Display:wght@400;600;700&family=Merriweather:wght@400;700&family=Lora:wght@400;600&family=Roboto+Slab:wght@400;600&family=Open+Sans:wght@400;600&family=Source+Sans+3:wght@400;600&family=Nunito:wght@400;700&family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* BASE RESET & EXTERNAL STYLES */
        ${externalCSS}

        /* ROOT VARIABLES & OVERRIDES */
        ${rootVarsCSS}

        /* Essential Layout Overrides for Export */
        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* NUCLEAR OVERRIDE: Force full-width for export */
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: auto !important;
            min-height: 100vh !important;
            overflow-x: hidden !important;
            background: var(--global-section-bg, #ffffff) !important;
        }

        .wireframe-page-column,
        body .wireframe-page-column,
        .bp-desktop .wireframe-page-column,
        .bp-tablet .wireframe-page-column,
        .bp-mobile .wireframe-page-column {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            min-height: 100vh !important;
            background: var(--global-section-bg, #ffffff) !important;
            box-shadow: none !important;
            border: none !important;
        }

        .page-column-content {
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Ensure sections take full width and remove separation lines */
        .wireframe-section {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            padding: var(--wfe-section-padding, 80px 0) !important;
            background: var(--global-section-bg, #ffffff) !important;
            display: flex !important;
            justify-content: center !important;
            border: none !important; /* Remove separation lines */
            box-shadow: none !important;
        }


        /* Remove 1200px constraint for TRUE full width if requested, 
           or keep it for content but ensure sections are full */
        .wireframe-section > div:not(.section-toolbar) {
            width: 100% !important;
            max-width: 1400px; /* Increased for wider feel, but keeping some structure */
            padding-left: 40px;
            padding-right: 40px;
            margin: 0 auto !important;
        }


        /* Typographic Resets for Export */
        .wireframe-section h1, .wireframe-section h2, .wireframe-section h3 { color: inherit; margin-bottom: 1rem; }
        .wireframe-section h1 { font-size: 48px; font-weight: 700; }
        .wireframe-section h2 { font-size: 32px; font-weight: 700; }
        .wireframe-section h3 { font-size: 24px; font-weight: 600; }

        .wireframe-section p, .wireframe-section span, .wireframe-section li, .wireframe-section div { color: inherit; }
        .wireframe-section p { margin-bottom: 1.5rem; max-width: 65ch; font-size: 18px; opacity: 0.9; }

        /* Specific Component Layout Adjustments */
        .hero-wireframe { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; color: inherit; }
        .hero-image .image-placeholder { background: #f1f5f9; border-radius: 8px; height: 450px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 20px; border: 2px dashed #e2e8f0; }

        .cta-button { padding: 14px 36px; background: var(--wfe-btn-bg, #3b82f6); color: var(--wfe-btn-text, #fff) !important; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer; display: inline-block; text-decoration: none; }

        .navbar-wireframe { display: flex; justify-content: space-between; align-items: center; padding: 24px 0; color: inherit; }
        .nav-logo { font-size: 22px; font-weight: 800; color: inherit; }
        .nav-links { display: flex; gap: 12px; }
        .nav-link { padding: 8px 16px; background: rgba(0,0,0,0.05); border-radius: 4px; font-weight: 600; color: inherit !important; text-decoration: none; }
        
        /* Grid Fixes */
        .features-grid { display: grid; gap: 24px; margin-top: 40px; color: inherit; }
        
        .feature-item { padding: 32px; background: #ffffff; border-radius: 16px; text-align: left; display: flex; flex-direction: column; align-items: flex-start; gap: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.05); color: var(--wfe-text-color) !important; }
        
        .feature-icon { font-size: 28px; width: 56px; height: 56px; background: #f8fafc; border-radius: 14px; display: flex; align-items: center; justify-content: center; border: 1px solid #eef2f7; }

        .footer-wireframe { display: grid; grid-template-columns: repeat(4, 1fr); gap: 40px; padding: 60px 0; border-top: 1px solid rgba(0,0,0,0.1); color: inherit; }
        .footer-wireframe a { color: inherit; text-decoration: none; }
        .footer-wireframe h5 { font-size: 18px; font-weight: 700; color: inherit; }

        @media (max-width: 992px) { 
            .hero-wireframe { grid-template-columns: 1fr; text-align: center; } 
            .footer-wireframe { grid-template-columns: repeat(2, 1fr); } 
            .features-grid { grid-template-columns: 1fr !important; } 
        }
    </style>
</head>
<body>
    <div class="wireframe-page-column">
        <div class="page-column-content">
            ${contentClone.innerHTML}
        </div>
    </div>

    <!-- RESPONSIVE HELPERS -->
    <script>
        function updateLayout() {
            const width = window.innerWidth;
            document.body.classList.remove('bp-desktop', 'bp-tablet', 'bp-mobile');
            
            if (width >= 1024) {
                document.body.classList.add('bp-desktop');
            } else if (width >= 768) {
                document.body.classList.add('bp-tablet');
            } else {
                document.body.classList.add('bp-mobile');
            }
        }

        window.addEventListener('resize', updateLayout);
        window.addEventListener('load', updateLayout);
    </script>
</body>
</html>`;

        return html;
    }
}


if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WireframeApp };
}

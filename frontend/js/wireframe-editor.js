// Enhanced Wireframe Editor with Two-Way Sync
class WireframeEditor {
    constructor() {
        this.currentPageId = null;
        this.currentBreakpoint = 'desktop';
        this.editMode = false;
        this.activeSection = null; // Track currently editing section
        this.globalStyles = { palette: null, fontFamily: 'Inter, sans-serif', logoUrl: null };
        this.init();
    }

    init() {
        this.bindEvents();
        this.bindSidebarControls(); // Bind sidebar inputs
        this.bindGlobalStyleControls();
        this.setupStateSync();
    }

    bindEvents() {
        // Global Style: open/close
        const globalBtn = document.getElementById('globalStyleBtn');
        if (globalBtn) {
            globalBtn.addEventListener('click', () => this.openGlobalStyleSidebar());
        }
        const closeGlobalStyleBtn = document.getElementById('closeGlobalStyleBtn');
        if (closeGlobalStyleBtn) {
            closeGlobalStyleBtn.addEventListener('click', () => this.closeGlobalStyleSidebar());
        }

        const screenSizeSelect = document.getElementById('screenSizeSelect');
        if (screenSizeSelect) {
            screenSizeSelect.addEventListener('change', (e) => {
                this.setBreakpoint(e.target.value);
            });
        }
        const zoomSelect = document.getElementById('zoomSelect');
        if (zoomSelect) {
            zoomSelect.addEventListener('change', (e) => {
                this.setZoom(parseFloat(e.target.value));
            });
        }

        // Open extended panels
        const colorsCard = document.getElementById('styleColorsCard');
        if (colorsCard) colorsCard.addEventListener('click', () => this.openColorsPanel());
        const fontsCard = document.getElementById('styleFontsCard');
        if (fontsCard) fontsCard.addEventListener('click', () => this.openFontsPanel());

        const colorsBackBtn = document.getElementById('colorsBackBtn');
        const colorsCloseBtn = document.getElementById('colorsCloseBtn');
        if (colorsBackBtn) colorsBackBtn.addEventListener('click', () => this.closeColorsPanel());
        if (colorsCloseBtn) colorsCloseBtn.addEventListener('click', () => this.closeColorsPanel());
        const fontsBackBtn = document.getElementById('fontsBackBtn');
        const fontsCloseBtn = document.getElementById('fontsCloseBtn');
        if (fontsBackBtn) fontsBackBtn.addEventListener('click', () => this.closeFontsPanel());
        if (fontsCloseBtn) fontsCloseBtn.addEventListener('click', () => this.closeFontsPanel());


        // Edit mode toggle
        const editToggle = document.getElementById('editModeToggle');
        if (editToggle) {
            editToggle.addEventListener('click', () => {
                this.toggleEditMode();
            });
        }

        // Sidebar close button
        const closeSidebarBtn = document.getElementById('closeSidebarBtn');
        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', () => {
                this.closeSidebar();
            });
        }

        // Initialize Tabs and Accordions with robust handlers
        this.initializeSidebarTabs();
        this.initializeAccordions();

        // Component Replacement View Toggles
        const replaceTrigger = document.getElementById('componentCardTrigger');
        if (replaceTrigger) {
            replaceTrigger.addEventListener('click', () => this.openReplaceView());
        }

        const backToSettingsBtn = document.getElementById('backToSettingsBtn');
        if (backToSettingsBtn) {
            backToSettingsBtn.addEventListener('click', () => this.closeReplaceView());
        }

        const closeReplaceBtn = document.getElementById('closeReplaceViewBtn');
        if (closeReplaceBtn) {
            closeReplaceBtn.addEventListener('click', () => this.closeSidebar());
        }

        const shuffleComponentBtn = document.getElementById('shuffleComponentBtn');
        if (shuffleComponentBtn) {
            shuffleComponentBtn.addEventListener('click', () => this.shuffleLayout());
        }

        // Delegated listener for inline edits
        const board = document.getElementById('wireframeBoard');
        if (board) {
            board.addEventListener('input', (e) => {
                if (e.target.classList.contains('editable-text')) {
                    this.handleInlineEdit(e.target);
                }
            });
        }
    }

    // Bind sidebar inputs to real-time updates
    bindSidebarControls() {
        // Design Tab Inputs
        const styleInputs = {
            'fontFamilySelect': 'fontFamily',
            'textColorInput': 'textColor',
            'fontSizeInput': 'fontSize',
            'fontWeightSelect': 'fontWeight',
            'bgColorInput': 'backgroundColor',
            'paddingInput': 'padding',
            'marginInput': 'margin',
            'btnColorInput': 'btnColor',
            'btnTextColorInput': 'btnTextColor',
            'btnRadiusInput': 'btnRadius',
            'btnSizeSelect': 'btnSize'
        };

        for (const [inputId, styleProp] of Object.entries(styleInputs)) {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', (e) => {
                    this.handleStyleChange(styleProp, e.target.value);

                    // Update color value display if it's a color input
                    if (e.target.type === 'color') {
                        const valueSpan = e.target.nextElementSibling;
                        if (valueSpan && valueSpan.classList.contains('color-value')) {
                            valueSpan.textContent = e.target.value;
                        }
                    }
                });
            }
        }

        // Layout Variant Input
        const layoutSelect = document.getElementById('layoutVariantSelect');
        if (layoutSelect) {
            layoutSelect.addEventListener('change', (e) => {
                this.handleLayoutVariantChange(e.target.value);
            });
        }

        // Content Tab Inputs
        const contentInputs = {
            'sectionNameInput': 'title',
            'sectionDescInput': 'description',
            'buttonLabelInput': 'buttonText'
        };

        for (const [inputId, field] of Object.entries(contentInputs)) {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', (e) => {
                    this.handleContentChange(field, e.target.value);
                });
            }
        }

        // Action Buttons
        const shuffleBtn = document.getElementById('shuffleLayoutBtn');
        if (shuffleBtn) {
            shuffleBtn.addEventListener('click', () => this.shuffleLayout());
        }

        const regenerateBtn = document.getElementById('regenerateContentBtn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.regenerateContent());
        }

        const deleteSectionBtn = document.getElementById('deleteSectionBtn');
        if (deleteSectionBtn) {
            deleteSectionBtn.addEventListener('click', () => {
                if (this.activeSection) {
                    this.deleteSection(this.activeSection.pageId, this.activeSection.index);
                    this.closeSidebar();
                }
            });
        }

        // Logo Upload
        const logoInput = document.getElementById('logoUploadInput');
        if (logoInput) {
            logoInput.addEventListener('change', (e) => this.handleLogoUpload(e));
        }
    }

    // Global style controls
    bindGlobalStyleControls() {
        const paletteBar = document.getElementById('globalPaletteBar');
        if (paletteBar) {
            const palettes = [
                ['#92400e', '#f3b37a', '#f59e0b', '#b45309'],
                ['#0ea5e9', '#e0f2fe', '#0284c7', '#0369a1'],
                ['#10b981', '#d1fae5', '#059669', '#047857']
            ];
            const current = palettes[0];
            paletteBar.innerHTML = current.map(c => `<div style="background:${c}"></div>`).join('');
            paletteBar.addEventListener('click', () => {
                const idx = palettes.indexOf(current);
                const next = palettes[(idx + 1) % palettes.length];
                paletteBar.innerHTML = next.map(c => `<div style="background:${c}"></div>`).join('');
                this.applyGlobalStyles({
                    textColor: next[3],
                    backgroundColor: next[1],
                    btnColor: next[2],
                    btnTextColor: '#ffffff'
                });
            });
        }

        const fontPreview = document.getElementById('fontPreview');
        if (fontPreview) {
            const fonts = ['Inter, sans-serif', 'Arial, sans-serif', "'Times New Roman', serif", 'Georgia, serif'];
            let fi = 0;
            const applyFont = (font) => {
                fontPreview.style.fontFamily = font;
                this.applyGlobalStyles({ fontFamily: font });
            };
            applyFont(fonts[fi]);
            fontPreview.addEventListener('click', () => {
                fi = (fi + 1) % fonts.length;
                applyFont(fonts[fi]);
            });
        }

        const logoInput = document.getElementById('globalLogoInput');
        const logoBox = document.getElementById('logoBox');
        if (logoBox) {
            logoBox.addEventListener('click', () => {
                if (logoInput) logoInput.click();
            });
        }
        if (logoInput) {
            logoInput.addEventListener('change', (e) => {
                const file = e.target.files && e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => {
                    const logoUrl = ev.target.result;
                    this.globalStyles.logoUrl = logoUrl;
                    document.querySelectorAll('.wireframe-section.navbar .nav-logo span, .wireframe-section.header .nav-logo span').forEach(el => {
                        const img = document.createElement('img');
                        img.src = logoUrl;
                        img.style.maxHeight = '40px';
                        el.innerHTML = '';
                        el.appendChild(img);
                    });
                    if (logoBox) {
                        logoBox.innerHTML = '';
                        const img2 = document.createElement('img');
                        img2.src = logoUrl;
                        img2.style.maxHeight = '40px';
                        logoBox.appendChild(img2);
                    }
                    if (window.stateManager && window.stateManager.getSitemap()) {
                        const sm = window.stateManager.getSitemap();
                        sm.styles = sm.styles || {};
                        sm.styles.logoUrl = logoUrl;
                        window.stateManager.setSitemap(sm);
                    }
                };
                reader.readAsDataURL(file);
            });
        }
    }

    openGlobalStyleSidebar() {
        const el = document.getElementById('globalStyleSidebar');
        if (el) el.classList.add('active');
        const main = document.querySelector('.wireframe-main');
        if (main) main.classList.add('global-style-open');
    }

    closeGlobalStyleSidebar() {
        const el = document.getElementById('globalStyleSidebar');
        if (el) el.classList.remove('active');
        const main = document.querySelector('.wireframe-main');
        if (main) main.classList.remove('global-style-open');
    }

    // --- Global Style Management (CSS Variables) ---
    applyGlobalStyles(styles) {
        this.globalStyles = { ...this.globalStyles, ...styles };
        if (!styles) return;

        console.log('🌈 Applying global styles to all pages...');

        // 1. Force update the root CSS variables for instant visual change
        this.updateGlobalVariables(styles);

        // 2. SAVE TO STATE MANAGER
        if (window.stateManager) {
            const sm = window.stateManager.getSitemap();
            if (sm) {
                // Ensure styles object exists
                sm.styles = { ...(sm.styles || {}), ...styles };

                // Update global styles in state
                window.stateManager.setSitemap(sm);
                console.log('💾 Global styles saved to state:', sm.styles);
            }
        }

        // 3. CLEANUP: Force remove backgroundColor, background, and backgroundImage from all sections in the sitemap state
        // to ensure no persistent overrides are saved (except for specific section overrides if we wanted to keep them, but here we prioritize global)
        if (window.stateManager) {
            const sm = window.stateManager.getState();
            if (sm && sm.pages) {
                const cleanSections = (pages) => {
                    pages.forEach(p => {
                        if (p.sections) {
                            p.sections.forEach(s => {
                                if (s.styles) {
                                    // Remove all possible background overrides from state so Global takes precedence
                                    delete s.styles.backgroundColor;
                                    delete s.styles.background;
                                    delete s.styles.backgroundImage;
                                    delete s.styles.hifiInit;
                                }
                            });
                        }
                        if (p.children) cleanSections(p.children);
                    });
                };
                cleanSections(sm.pages);
                // Save the cleaned state
                window.stateManager.setState(sm);
            }
        }
    }

    updateGlobalVariables(styles) {
        const root = document.documentElement;
        // Bind 'backgroundColor' in Global Styles to the GLOBAL SECTION BACKGROUND variable
        if (styles.backgroundColor) root.style.setProperty('--global-section-bg', styles.backgroundColor);

        if (styles.textColor) root.style.setProperty('--wfe-text-color', styles.textColor);
        if (styles.btnColor) {
            root.style.setProperty('--wfe-btn-bg', styles.btnColor);
            // Also update any other primary color related variables if needed
        }
        if (styles.btnTextColor) root.style.setProperty('--wfe-btn-text', styles.btnTextColor);
        if (styles.headingFont) root.style.setProperty('--wfe-font-heading', styles.headingFont);
        if (styles.paragraphFont) root.style.setProperty('--wfe-font-body', styles.paragraphFont);

        // Ensure ALL sections across ALL pages are refreshed visually
        document.querySelectorAll('.wireframe-section').forEach(sectionEl => {
            // Re-apply common properties to ensure consistency
            const elementStyles = sectionEl.styles || {};
            this.applyStylesToElement(sectionEl, elementStyles);
        });
    }

    // Single consistent definition
    applyStylesToAllSections(styles) {
        // Now handled via updateGlobalVariables
        this.applyGlobalStyles(styles);
    }

    applyStylesToActiveSection(styles) {
        if (!this.activeSection) return;
        const el = this.activeSection.element;
        const merged = { ...(this.activeSection.section.styles || {}), ...styles };
        this.activeSection.section.styles = merged;
        this.applyStylesToElement(el, merged);
        this.saveStyles(merged);
    }

    applyStylesToPage(pageId, styles) {
        const column = document.querySelector(`.wireframe-page-column[data-page-id="${pageId}"]`);
        if (!column) return;
        column.querySelectorAll('.wireframe-section').forEach(sectionEl => {
            this.applyStylesToElement(sectionEl, styles);
        });
    }

    setBreakpoint(bp) {
        this.currentBreakpoint = bp;
        const board = document.getElementById('wireframeBoard');
        if (!board) return;
        board.classList.remove('bp-desktop', 'bp-tablet', 'bp-mobile');
        switch (bp) {
            case 'tablet':
                board.classList.add('bp-tablet');
                break;
            case 'mobile':
                board.classList.add('bp-mobile');
                break;
            default:
                board.classList.add('bp-desktop');
        }
    }

    setZoom(scale) {
        const board = document.getElementById('wireframeBoard');
        if (!board) return;
        if (scale === 1) {
            board.classList.remove('board-zoomed');
            board.style.transform = 'none';
            board.style.transformOrigin = '';
        } else {
            board.classList.add('board-zoomed');
            board.style.transformOrigin = '0 0';
            board.style.transform = `scale(${scale})`;
        }
    }

    openColorsPanel() {
        const panel = document.getElementById('colorsPanel');
        if (panel) {
            panel.classList.add('active');
            this.populateColorsPanel();
        }
    }
    closeColorsPanel() {
        const panel = document.getElementById('colorsPanel');
        if (panel) panel.classList.remove('active');
    }
    openFontsPanel() {
        const panel = document.getElementById('fontsPanel');
        if (panel) {
            panel.classList.add('active');
            this.populateFontsPanel();
        }
    }
    closeFontsPanel() {
        const panel = document.getElementById('fontsPanel');
        if (panel) panel.classList.remove('active');
    }

    populateColorsPanel() {
        const currentPaletteBar = document.getElementById('currentPaletteBar');
        const suggestedGrid = document.getElementById('suggestedPaletteGrid');
        const prevBtn = document.getElementById('palettePrevBtn');
        const nextBtn = document.getElementById('paletteNextBtn');
        const suggestMoreBtn = document.getElementById('suggestMoreColorsBtn');
        const chipRow = document.querySelectorAll('.chip-row .chip');
        const pages = [
            [
                ['#073b4c', '#ffd9cf', '#e63946', '#6b1d1d'],
                ['#3b82f6', '#e9d8a6', '#8b5e34', '#4b3f2f'],
                ['#fb923c', '#f1dfd0', '#6b1d1d', '#3c0d0d'],
                ['#b59f3b', '#f0e2c4', '#5a2e1b', '#2e130c']
            ],
            [
                ['#0ea5e9', '#f5f5f4', '#ef4444', '#7c2d12'],
                ['#14b8a6', '#e2e8f0', '#3b82f6', '#111827'],
                ['#f59e0b', '#fff7ed', '#1f2937', '#374151'],
                ['#6d28d9', '#ede9fe', '#1e293b', '#0f172a']
            ]
        ];
        let pageIndex = 0;
        const renderCurrent = (palette) => {
            currentPaletteBar.innerHTML = palette.map(c => `<div style="background:${c}"></div>`).join('');
        };
        const renderSuggested = () => {
            suggestedGrid.innerHTML = pages[pageIndex].map(p => `
                <div class="palette-item" data-palette='${JSON.stringify(p)}'>
                    <div class="palette-bar">${p.map(c => `<div style="background:${c}"></div>`).join('')}</div>
                </div>
            `).join('');
            suggestedGrid.querySelectorAll('.palette-item').forEach(item => {
                item.addEventListener('click', () => {
                    const palette = JSON.parse(item.dataset.palette);
                    renderCurrent(palette);
                    const styles = {
                        textColor: palette[3], backgroundColor: palette[1],
                        btnColor: palette[2], btnTextColor: '#ffffff'
                    };
                    this.applyGlobalStyles(styles);
                });
            });
        };
        renderCurrent(pages[pageIndex][0]);
        renderSuggested();
        if (prevBtn) prevBtn.onclick = () => { pageIndex = (pageIndex + pages.length - 1) % pages.length; renderSuggested(); };
        if (nextBtn) nextBtn.onclick = () => { pageIndex = (pageIndex + 1) % pages.length; renderSuggested(); };
        if (suggestMoreBtn) suggestMoreBtn.onclick = () => {
            const rand = Array.from({ length: 4 }, () => `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`);
            pages.push([rand, rand.slice().reverse(), rand.map((c, i) => i % 2 ? c : '#ffffff'), rand.map((c, i) => i % 2 ? c : '#000000')]);
            pageIndex = pages.length - 1;
            renderSuggested();
        };
        chipRow.forEach(chip => {
            chip.addEventListener('click', () => {
                const col = chip.getAttribute('data-color');
                this.applyGlobalStyles({ backgroundColor: col });
            });
        });
    }

    lighten(hex, ratio) {
        const n = hex.replace('#', '');
        const r = parseInt(n.substring(0, 2), 16);
        const g = parseInt(n.substring(2, 4), 16);
        const b = parseInt(n.substring(4, 6), 16);
        const rr = Math.round(r + (255 - r) * ratio);
        const gg = Math.round(g + (255 - g) * ratio);
        const bb = Math.round(b + (255 - b) * ratio);
        return `rgb(${rr}, ${gg}, ${bb})`;
    }



    populateFontsPanel() {
        const headingSel = document.getElementById('headingFontSelect');
        const paraSel = document.getElementById('paragraphFontSelect');
        const previewH = document.getElementById('currentHeadingPreview');
        const previewP = document.getElementById('currentParagraphPreview');
        const suggestionsEl = document.getElementById('fontSuggestions');
        const labelOf = (f) => (f || '').replace(/,.*/, '').replace(/['"]/g, '');
        const pairs = [
            { h: "'Tiro Devanagari Hindi', serif", p: "'Poppins', sans-serif" },
            { h: "Georgia, serif", p: "Inter, sans-serif" },
            { h: "'Times New Roman', serif", p: "Arial, sans-serif" },
            { h: "Inter, sans-serif", p: "'Poppins', sans-serif" },
            { h: "'Abril Fatface', serif", p: "'Poppins', sans-serif" },
            { h: "'Playfair Display', serif", p: "'Open Sans', sans-serif" },
            { h: "'Merriweather', serif", p: "'Source Sans 3', sans-serif" },
            { h: "'Lora', serif", p: "Inter, sans-serif" },
            { h: "'Roboto Slab', serif", p: "'Poppins', sans-serif" },
            { h: "'Montserrat', sans-serif", p: "'Nunito', sans-serif" },
            { h: "Georgia, serif", p: "'Poppins', sans-serif" },
            { h: "'Times New Roman', serif", p: "'Poppins', sans-serif" }
        ];
        const applyPair = (pair) => {
            previewH.style.fontFamily = pair.h;
            previewP.style.fontFamily = pair.p;
            previewH.textContent = labelOf(pair.h);
            previewP.textContent = labelOf(pair.p);
            if (headingSel) headingSel.value = pair.h;
            if (paraSel) paraSel.value = pair.p;
            this.applyFontsGlobally(pair.h, pair.p);
        };
        applyPair(pairs[0]);
        suggestionsEl.innerHTML = pairs.map((pair, i) => {
            const lh = labelOf(pair.h), lp = labelOf(pair.p);
            return `
                <div class="font-pair-card" data-idx="${i}" title="Heading: ${lh} • Paragraph: ${lp}" style="padding:10px;border:1px solid #e2e8f0;border-radius:6px;">
                    <div class="font-pair-heading" style="font-family:${pair.h}">Heading</div>
                    <div class="font-pair-paragraph" style="font-family:${pair.p}">Paragraph</div>
                    <div class="font-pair-labels" style="display:flex;gap:6px;font-size:12px;color:#64748b;margin-top:4px;">
                        <span>${lh}</span><span>•</span><span>${lp}</span>
                    </div>
                </div>
            `;
        }).join('');
        suggestionsEl.querySelectorAll('.font-pair-card').forEach(card => {
            card.addEventListener('click', () => {
                const idx = parseInt(card.dataset.idx, 10);
                applyPair(pairs[idx]);
            });
        });
        const suggestMore = document.getElementById('suggestMoreFontsBtn');
        if (suggestMore) suggestMore.onclick = () => {
            const extra = { h: "Georgia, serif", p: "'Poppins', sans-serif" };
            pairs.push(extra);
            const card = document.createElement('div');
            card.className = 'font-pair-card';
            card.innerHTML = `
                <div class="font-pair-heading" style="font-family:${extra.h}">Heading</div>
                <div class="font-pair-paragraph" style="font-family:${extra.p}">Paragraph</div>
                <div class="font-pair-labels" style="display:flex;gap:6px;font-size:12px;color:#64748b;margin-top:4px;">
                    <span>${labelOf(extra.h)}</span><span>•</span><span>${labelOf(extra.p)}</span>
                </div>
            `;
            card.title = `Heading: ${labelOf(extra.h)} • Paragraph: ${labelOf(extra.p)}`;
            card.addEventListener('click', () => applyPair(extra));
            suggestionsEl.appendChild(card);
        };
        if (headingSel) headingSel.onchange = (e) => applyPair({ h: e.target.value, p: paraSel ? paraSel.value : "'Poppins', sans-serif" });
        if (paraSel) paraSel.onchange = (e) => applyPair({ h: headingSel ? headingSel.value : "Inter, sans-serif", p: e.target.value });
    }

    applyFontsGlobally(headingFont, paragraphFont) {
        document.querySelectorAll('.wireframe-section').forEach(el => {
            if (paragraphFont) {
                el.style.fontFamily = paragraphFont;
            }
            el.querySelectorAll('.section-content h1, .section-content h2, .section-content h3, .section-content h4, .section-content h5, .section-content h6, .hero-wireframe h1, .features-wireframe h2, .navbar-wireframe .nav-logo span, .font-pair-heading').forEach(node => { node.style.fontFamily = headingFont; });
            el.querySelectorAll('.section-content p, .section-content span, .section-content li, .hero-wireframe p, .features-wireframe p, .navbar-wireframe .nav-link, .font-pair-paragraph').forEach(node => { node.style.fontFamily = paragraphFont; });
        });
        if (window.stateManager && window.stateManager.getSitemap()) {
            const sm = window.stateManager.getSitemap();
            if (sm && sm.pages) {
                sm.pages.forEach(page => {
                    if (!page.sections) return;
                    page.sections.forEach((section, index) => {
                        const styles = { ...(section.styles || {}), headingFont, paragraphFont };
                        window.stateManager.updateSection(page.id, index, { styles });
                    });
                });
            }
            sm.styles = { ...(sm.styles || {}), headingFont, paragraphFont };
            window.stateManager.setSitemap(sm);
        }
    }

    // Handled via updateGlobalVariables
    // applyStylesToAllSections removed from here (duplicate)
    handleStyleChange(property, value) {
        if (!this.activeSection) return;

        // Update local element immediately for preview
        const styles = this.activeSection.section.styles || {};
        styles[property] = value;
        this.activeSection.section.styles = styles;

        this.applyStylesToElement(this.activeSection.element, styles);

        // Persist change (debounced)
        if (this.styleSaveTimer) clearTimeout(this.styleSaveTimer);

        this.styleSaveTimer = setTimeout(() => {
            if (window.stateManager) {
                window.stateManager.updateSection(
                    this.activeSection.pageId,
                    this.activeSection.index,
                    { styles: styles }
                );
            }
        }, 500);
    }

    handleContentChange(field, value) {
        if (!this.activeSection) return;

        // Update DOM
        const el = this.activeSection.element;
        if (field === 'title') {
            const titleEl = el.querySelector('[data-field="title"]');
            if (titleEl) titleEl.textContent = value;
        } else if (field === 'description') {
            const descEl = el.querySelector('[data-field="description"]');
            if (descEl) descEl.textContent = value;
        } else if (field === 'buttonText') {
            const btn = el.querySelector('.cta-button, .btn');
            if (btn) btn.textContent = value;
        }

        // Update State
        if (window.stateManager) {
            const updates = {};
            updates[field] = value;
            window.stateManager.updateSection(
                this.activeSection.pageId,
                this.activeSection.index,
                updates
            );
        }
    }

    handleLayoutVariantChange(variant) {
        if (!this.activeSection) return;

        const section = this.activeSection.section;
        section.layoutVariant = variant;

        // Update the DOM by re-rendering the section content
        const content = this.createSectionContent(section, this.activeSection.index, this.activeSection.pageId);
        const contentContainer = this.activeSection.element.querySelector('.section-content');
        if (contentContainer) {
            contentContainer.replaceWith(content);
        }

        // Update State
        if (window.stateManager) {
            window.stateManager.updateSection(
                this.activeSection.pageId,
                this.activeSection.index,
                { layoutVariant: variant }
            );
        }
    }

    handleInlineEdit(target) {
        const sectionEl = target.closest('.wireframe-section');
        if (!sectionEl || !window.stateManager) return;

        const pageId = sectionEl.dataset.pageId;
        const index = parseInt(sectionEl.dataset.sectionIndex, 10);
        const field = target.dataset.field;
        const value = target.textContent;

        const updates = {};

        if (field === 'item-title' || field === 'item-desc') {
            const itemIndex = parseInt(target.dataset.index, 10);
            const page = window.stateManager.findPageById(pageId);
            if (page && page.sections[index]) {
                const section = page.sections[index];
                if (!section.items) section.items = [];
                if (!section.items[itemIndex]) section.items[itemIndex] = {};

                const itemField = field === 'item-title' ? 'title' : 'desc';
                section.items[itemIndex][itemField] = value;
                updates.items = section.items;
            }
        } else {
            updates[field] = value;
        }

        window.stateManager.updateSection(pageId, index, updates);
    }

    shuffleLayout() {
        if (!this.activeSection) return;

        const el = this.activeSection.element;
        // Toggle between standard and alternate layout
        // We find the main content container which usually has the grid/flex display
        const contentDiv = el.querySelector('.wireframe-element') || el.querySelector('.section-content > div');

        if (contentDiv) {
            contentDiv.classList.toggle('layout-alt');

            // Save state
            const styles = this.activeSection.section.styles || {};
            styles.layout = contentDiv.classList.contains('layout-alt') ? 'alt' : 'default';
            this.activeSection.section.styles = styles;

            this.saveStyles(styles);
        }
    }

    regenerateContent() {
        if (!this.activeSection) return;

        const type = this.activeSection.section.type;
        const newContent = this.getMockContent(type);

        // Update Title
        if (newContent.title) {
            this.handleContentChange('title', newContent.title);
            // Also update input in sidebar
            const titleInput = document.getElementById('sectionNameInput');
            if (titleInput) titleInput.value = newContent.title;
        }

        // Update Description
        if (newContent.description) {
            this.handleContentChange('description', newContent.description);
            // Also update input in sidebar
            const descInput = document.getElementById('sectionDescInput');
            if (descInput) descInput.value = newContent.description;
        }

        // Update Button Text
        if (newContent.buttonText) {
            this.handleContentChange('buttonText', newContent.buttonText);
            const btnInput = document.getElementById('buttonLabelInput');
            if (btnInput) btnInput.value = newContent.buttonText;
        }
    }

    getMockContent(type) {
        const content = {
            hero: {
                title: [
                    "Transform Your Digital Presence",
                    "Build Faster, Scale Better",
                    "The Future of Web Design is Here"
                ],
                description: [
                    "Empower your team with the tools they need to succeed in a digital-first world.",
                    "Streamline your workflow and boost productivity with our innovative solutions.",
                    "Create stunning experiences that captivate your audience and drive growth."
                ],
                buttonText: ["Get Started", "Learn More", "Try for Free"]
            },
            features: {
                title: [
                    "Why Choose Us",
                    "Key Features",
                    "Everything You Need"
                ],
                description: [
                    "Discover the powerful features that set us apart from the competition.",
                    "A comprehensive suite of tools designed to help you grow.",
                    "Built for performance, scalability, and ease of use."
                ],
                buttonText: ["View Features", "See Details", "Explore All"]
            },
            testimonial: {
                title: [
                    "Trusted by Thousands",
                    "What Our Clients Say",
                    "Success Stories"
                ],
                description: [
                    "\"This platform changed the way we work. Highly recommended!\"",
                    "\"Incredible support and amazing features. A game changer.\"",
                    "\"The best investment we've made for our business this year.\""
                ],
                buttonText: ["Read More", "View Case Studies", "Join Them"]
            }
        };

        const options = content[type] || content.hero; // Fallback to hero

        const getRandom = (arr) => arr[Math.floor(Math.random() * arr.length)];

        return {
            title: getRandom(options.title),
            description: getRandom(options.description),
            buttonText: getRandom(options.buttonText)
        };
    }

    // Helper to save styles (deduplicated logic)
    saveStyles(styles) {
        if (this.styleSaveTimer) clearTimeout(this.styleSaveTimer);
        this.styleSaveTimer = setTimeout(() => {
            if (window.stateManager) {
                window.stateManager.updateSection(
                    this.activeSection.pageId,
                    this.activeSection.index,
                    { styles: styles }
                );
            }
        }, 500);
    }

    handleLogoUpload(e) {
        if (!this.activeSection || !e.target.files[0]) return;

        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = (event) => {
            const logoUrl = event.target.result;
            // Find logo element
            const logoEl = this.activeSection.element.querySelector('.nav-logo span');
            if (logoEl) {
                // Replace text with image
                const img = document.createElement('img');
                img.src = logoUrl;
                img.style.maxHeight = '40px';
                logoEl.innerHTML = '';
                logoEl.appendChild(img);

                // Save state
                // This assumes state supports logoUrl or similar
            }
        };
        reader.readAsDataURL(file);
    }

    openStyleSidebar(section, index, pageId, element) {
        // Deselect previous
        if (this.activeSection && this.activeSection.element) {
            this.activeSection.element.classList.remove('selected');
        }

        this.activeSection = { section, index, pageId, element };
        element.classList.add('selected');

        const sidebar = document.getElementById('sectionSettingsSidebar');
        const mainView = document.getElementById('sidebarMainView');
        const replaceView = document.getElementById('sidebarReplaceView');

        if (sidebar) {
            sidebar.classList.add('active');
            // Ensure main view is active
            if (mainView) mainView.classList.add('active');
            if (replaceView) replaceView.classList.remove('active');
        }

        // Update Component Name
        const nameEl = document.getElementById('sidebarComponentName');
        if (nameEl) nameEl.textContent = section.type.charAt(0).toUpperCase() + section.type.slice(1);

        // Show/Hide Logo Upload based on section type
        const logoGroup = document.getElementById('logoUploadGroup');
        if (logoGroup) {
            logoGroup.style.display = (section.type === 'navbar' || section.type === 'header') ? 'block' : 'none';
        }

        // Populate Inputs
        this.populateSidebarInputs(section);

        // Switch to Design tab if style button was clicked (passed as arg maybe? for now default behavior)
        // Or just keep current tab.
        // Let's force Design tab if opened via Style button, Content tab if clicking section body (if we implement that)
        // For now, let's default to Design tab since we clicked "Style" button
        const designTabBtn = document.querySelector('.sidebar-tab[data-tab="design"]');
        if (designTabBtn) designTabBtn.click();
    }

    openReplaceView() {
        const replaceView = document.getElementById('sidebarReplaceView');
        if (replaceView) {
            replaceView.classList.add('active');
            this.populateReplaceList();
        }
    }

    closeReplaceView() {
        const replaceView = document.getElementById('sidebarReplaceView');
        if (replaceView) {
            replaceView.classList.remove('active');
        }
    }

    populateReplaceList() {
        const listContainer = document.getElementById('replaceComponentList');
        if (!listContainer || !this.activeSection) return;

        // Mock components based on current type or all types
        const currentType = this.activeSection.section.type;
        const components = this.getComponentOptions(currentType);

        listContainer.innerHTML = components.map(comp => `
            <div class="component-option" data-type="${comp.type}" data-variant="${comp.variant}">
                <div class="component-preview">
                    ${this.getComponentPreviewIcon(comp.type)}
                </div>
                <div class="component-info">
                    <span class="component-name">${comp.name}</span>
                </div>
            </div>
        `).join('');

        // Bind click events
        listContainer.querySelectorAll('.component-option').forEach(option => {
            option.addEventListener('click', () => {
                const type = option.dataset.type;
                const variant = option.dataset.variant; // Future use
                this.replaceComponent(type, variant);
            });
        });
    }

    getComponentOptions(type) {
        // Return list of available components
        // In a real app, this would be more dynamic
        const allComponents = [
            { type: 'hero', name: 'Hero Section', variant: 'default' },
            { type: 'navbar', name: 'Navbar', variant: 'default' },
            { type: 'features', name: 'Features Grid', variant: 'grid' },
            { type: 'content', name: 'Content Block', variant: 'default' },
            { type: 'testimonial', name: 'Testimonial', variant: 'default' },
            { type: 'cta', name: 'Call to Action', variant: 'default' },
            { type: 'footer', name: 'Footer', variant: 'default' }
        ];
        return allComponents;
    }

    getComponentPreviewIcon(type) {
        // Icons based on component type
        const icons = {
            hero: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                    <rect x="2" y="2" width="96" height="56" rx="4" fill="#f8fafc"/>
                    <rect x="20" y="15" width="60" height="6" rx="2" fill="#cbd5e1" stroke="none"/>
                    <rect x="30" y="25" width="40" height="4" rx="2" fill="#e2e8f0" stroke="none"/>
                    <rect x="40" y="35" width="20" height="8" rx="4" fill="#6366f1" stroke="none"/>
                   </svg>`,
            navbar: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                      <rect x="2" y="20" width="96" height="20" rx="4" fill="#f8fafc"/>
                      <circle cx="15" cy="30" r="4" fill="#6366f1" stroke="none"/>
                      <rect x="60" y="28" width="10" height="4" rx="2" fill="#cbd5e1" stroke="none"/>
                      <rect x="75" y="28" width="10" height="4" rx="2" fill="#cbd5e1" stroke="none"/>
                     </svg>`,
            features: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                        <rect x="10" y="10" width="24" height="40" rx="2" fill="#f8fafc"/>
                        <rect x="38" y="10" width="24" height="40" rx="2" fill="#f8fafc"/>
                        <rect x="66" y="10" width="24" height="40" rx="2" fill="#f8fafc"/>
                        <rect x="14" y="15" width="16" height="12" rx="2" fill="#e2e8f0" stroke="none"/>
                        <rect x="42" y="15" width="16" height="12" rx="2" fill="#e2e8f0" stroke="none"/>
                        <rect x="70" y="15" width="16" height="12" rx="2" fill="#e2e8f0" stroke="none"/>
                       </svg>`,
            testimonial: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                           <rect x="15" y="15" width="70" height="30" rx="4" fill="#f8fafc"/>
                           <circle cx="25" cy="30" r="6" fill="#cbd5e1" stroke="none"/>
                           <rect x="35" y="25" width="40" height="4" rx="2" fill="#e2e8f0" stroke="none"/>
                           <rect x="35" y="33" width="30" height="4" rx="2" fill="#e2e8f0" stroke="none"/>
                          </svg>`,
            footer: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                      <rect x="2" y="30" width="96" height="28" rx="2" fill="#1e293b" stroke="none"/>
                      <rect x="10" y="40" width="20" height="4" rx="1" fill="#475569" stroke="none"/>
                      <rect x="40" y="40" width="15" height="4" rx="1" fill="#475569" stroke="none"/>
                      <rect x="60" y="40" width="15" height="4" rx="1" fill="#475569" stroke="none"/>
                     </svg>`,
            content: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                       <rect x="10" y="10" width="80" height="40" rx="2" fill="#f8fafc"/>
                       <rect x="20" y="20" width="30" height="20" rx="2" fill="#e2e8f0" stroke="none"/>
                       <rect x="55" y="20" width="30" height="4" rx="2" fill="#cbd5e1" stroke="none"/>
                       <rect x="55" y="28" width="25" height="4" rx="2" fill="#cbd5e1" stroke="none"/>
                       <rect x="55" y="36" width="20" height="4" rx="2" fill="#cbd5e1" stroke="none"/>
                      </svg>`,
            cta: `<svg width="100%" height="100%" viewBox="0 0 100 60" fill="none" stroke="#64748b" stroke-width="2">
                   <rect x="5" y="10" width="90" height="40" rx="4" fill="#f8fafc"/>
                   <rect x="25" y="20" width="50" height="6" rx="2" fill="#cbd5e1" stroke="none"/>
                   <rect x="35" y="35" width="30" height="10" rx="4" fill="#6366f1" stroke="none"/>
                  </svg>`
        };

        return icons[type] || icons.hero;
    }

    getSectionFallbackVisual(sectionType, index = 0) {
        const library = window.WireframeIconLibrary;
        if (library && typeof library.getSectionVisual === 'function') {
            return library.getSectionVisual(sectionType, index);
        }

        return {
            emoji: '+',
            iconName: 'sparkles',
            iconSvg: ''
        };
    }

    getTitleAwareFallbackText(title, context = 'section') {
        const label = (title || context || 'section').toString().trim();
        if (context === 'contact') {
            return `Use this area to explain how visitors can reach out about ${label.toLowerCase()} and what happens after they make contact.`;
        }
        if (context === 'form') {
            return `Collect the key details needed to respond clearly about ${label.toLowerCase()} and the visitor's requirements.`;
        }
        if (context === 'footer') {
            return `Support visitors with navigation, follow-up links, and contact options related to ${label.toLowerCase()}.`;
        }
        return `Use this section to explain ${label.toLowerCase()} with clear, relevant detail connected to the page goals.`;
    }

    replaceComponent(newType, variant) {
        if (!this.activeSection) return;

        const { section, index, pageId } = this.activeSection;

        // Update section type
        section.type = newType;
        // Reset specific content fields if needed, or keep them if compatible
        // For simplicity, we keep compatible fields (title, description)

        // Regenerate content
        const newContent = this.createSectionContent(section, index, pageId);

        // Replace in DOM
        const contentContainer = this.activeSection.element.querySelector('.section-content');
        if (contentContainer) {
            contentContainer.replaceWith(newContent);
        }

        // Update name in sidebar
        const nameEl = document.getElementById('sidebarComponentName');
        if (nameEl) nameEl.textContent = newType.charAt(0).toUpperCase() + newType.slice(1);

        // Update State
        if (window.stateManager) {
            window.stateManager.updateSection(pageId, index, { type: newType });
        }

        this.closeReplaceView();
    }

    closeSidebar() {
        const sidebar = document.getElementById('sectionSettingsSidebar');
        if (sidebar) sidebar.classList.remove('active');
        this.activeSection = null;
    }

    getLayoutVariantsForSection(sectionType) {
        sectionType = (sectionType || '').toLowerCase();

        // Alias common types for consistent variant selection
        if (sectionType === 'main-information' || sectionType.includes('main info')) sectionType = 'main-info';
        if (sectionType === 'supporting-content' || sectionType === 'supporting-information' || sectionType.includes('supporting')) sectionType = 'supporting-info';
        if (sectionType === 'info') sectionType = 'information';

        const variants = {
            'hero': [
                { value: 'layout-split-right', label: 'Split Right' },
                { value: 'layout-split-left', label: 'Split Left' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-full-bg', label: 'Full Background' },
                { value: 'layout-asymmetric', label: 'Asymmetric' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-bold-text', label: 'Bold Text' },
                { value: 'layout-video-bg', label: 'Video Background' },
                { value: 'layout-diagonal', label: 'Diagonal' },
                { value: 'layout-stacked', label: 'Stacked' }
            ],
            'navbar': [
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-centered-logo', label: 'Centered Logo' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-mega', label: 'Mega Menu' },
                { value: 'layout-sidebar', label: 'Sidebar' },
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-transparent', label: 'Transparent' },
                { value: 'layout-sticky', label: 'Sticky' },
                { value: 'layout-hamburger', label: 'Hamburger' },
                { value: 'layout-full-width', label: 'Full Width' }
            ],
            'main-info': [
                { value: 'layout-default', label: 'Default' },
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-grid-2', label: 'Grid 2 Columns' },
                { value: 'layout-grid-3', label: 'Grid View' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-list', label: 'List View' },
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-banner', label: 'Banner' },
                { value: 'layout-timeline', label: 'Timeline' }
            ],
            'supporting-info': [
                { value: 'layout-default', label: 'Default' },
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-grid-2', label: 'Grid 2 Columns' },
                { value: 'layout-grid-3', label: 'Grid Layout' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-list', label: 'List' },
                { value: 'layout-cards', label: 'Card Layout' },
                { value: 'layout-banner', label: 'Banner' },
                { value: 'layout-timeline', label: 'Timeline' }
            ],
            'footer': [
                { value: 'layout-multi-column', label: 'Multi Column' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-bar', label: 'Bar' },
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-newsletter', label: 'Newsletter' }
            ],
            'features': [
                { value: 'layout-grid-3', label: 'Grid 3 Columns' },
                { value: 'layout-grid-2', label: 'Grid 2 Columns' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-staggered', label: 'Staggered' },
                { value: 'layout-masonry', label: 'Masonry' },
                { value: 'layout-list', label: 'List' },
                { value: 'layout-bento', label: 'Bento' },
                { value: 'layout-carousel', label: 'Carousel' },
                { value: 'layout-tabs', label: 'Tabs' }
            ],
            'testimonial': [
                { value: 'layout-grid-3', label: 'Grid 3 Columns' },
                { value: 'layout-carousel', label: 'Carousel' },
                { value: 'layout-featured', label: 'Featured' },
                { value: 'layout-masonry', label: 'Masonry' },
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-split', label: 'Split' }
            ],
            'contact': [
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-map-large', label: 'Map Large' },
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-list', label: 'List' }
            ],
            'pricing': [
                { value: 'layout-3-tier', label: '3 Tier' },
                { value: 'layout-table', label: 'Table' },
                { value: 'layout-toggle', label: 'Toggle' },
                { value: 'layout-horizontal', label: 'Horizontal' }
            ],
            'gallery': [
                { value: 'layout-grid-3', label: 'Grid 3 Columns' },
                { value: 'layout-masonry', label: 'Masonry' },
                { value: 'layout-grid-2', label: 'Grid 2 Columns' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-horizontal', label: 'Horizontal' }
            ],
            'blog': [
                { value: 'layout-card-grid', label: 'Card Grid' },
                { value: 'layout-list-sidebar', label: 'List with Sidebar' },
                { value: 'layout-featured', label: 'Featured' }
            ],
            'stats': [
                { value: 'layout-counter', label: 'Counter' },
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-minimal', label: 'Minimal' }
            ],
            'cta': [
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-banner', label: 'Banner' },
                { value: 'layout-minimal', label: 'Minimal' }
            ],
            'services': [
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-grid-3', label: 'Grid 3 Columns' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-list', label: 'List' },
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-featured', label: 'Featured' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-carousel', label: 'Carousel' },
                { value: 'layout-masonry', label: 'Masonry' },
                { value: 'layout-tabs', label: 'Tabs' },
                { value: 'layout-split', label: 'Split' }
            ],
            'story': [
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-timeline', label: 'Timeline' },
                { value: 'layout-split', label: 'Split' }
            ],
            'team': [
                { value: 'layout-list', label: 'List' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-cards', label: 'Cards' }
            ],
            'culture': [
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-grid', label: 'Grid' },
                { value: 'layout-list', label: 'List' }
            ],
            'location': [
                { value: 'layout-simple', label: 'Simple' },
                { value: 'layout-map-large', label: 'Map Large' },
                { value: 'layout-split', label: 'Split' }
            ],
            'information': [
                { value: 'layout-grid', label: 'Grid' },
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-list', label: 'List' }
            ],
            'contact-details': [
                { value: 'layout-list', label: 'List' },
                { value: 'layout-split', label: 'Split' }
            ],
            'contact-form': [
                { value: 'layout-split', label: 'Split' },
                { value: 'layout-centered', label: 'Centered' },
                { value: 'layout-map-large', label: 'Map Large' },
                { value: 'layout-cards', label: 'Cards' },
                { value: 'layout-minimal', label: 'Minimal' },
                { value: 'layout-list', label: 'List' }
            ],
            'key-features': [
                { value: 'layout-grid-3', label: 'Grid 3 Columns' },
                { value: 'layout-grid-2', label: 'Grid 2 Columns' },
                { value: 'layout-grid-4', label: 'Grid 4 Columns' },
                { value: 'layout-horizontal', label: 'Horizontal' },
                { value: 'layout-staggered', label: 'Staggered' },
                { value: 'layout-masonry', label: 'Masonry' },
                { value: 'layout-list', label: 'List' },
                { value: 'layout-bento', label: 'Bento' },
                { value: 'layout-carousel', label: 'Carousel' },
                { value: 'layout-tabs', label: 'Tabs' }
            ]
        };
        return variants[sectionType] || [{ value: 'layout-default', label: 'Default' }];
    }

    populateSidebarInputs(section) {
        const styles = section.styles || {};

        const setVal = (id, val, defaultVal = '') => {
            const input = document.getElementById(id);
            if (input) {
                input.value = val || defaultVal;
                // Update color text if needed
                if (input.type === 'color') {
                    const valueSpan = input.nextElementSibling;
                    if (valueSpan && valueSpan.classList.contains('color-value')) {
                        valueSpan.textContent = input.value;
                    }
                }
            }
        };

        // Populate layout variant select based on section type
        const layoutSelect = document.getElementById('layoutVariantSelect');
        if (layoutSelect) {
            const sectionType = (section.type || '').toLowerCase();
            const variants = this.getLayoutVariantsForSection(sectionType);
            layoutSelect.innerHTML = variants.map(variant => `<option value="${variant.value}">${variant.label}</option>`).join('');
            setVal('layoutVariantSelect', section.layoutVariant || variants[0]?.value || 'layout-default');
        }

        setVal('fontFamilySelect', styles.fontFamily, 'Inter, sans-serif');
        setVal('textColorInput', styles.textColor, '#1e293b');
        setVal('fontSizeInput', styles.fontSize, '16');
        setVal('fontWeightSelect', styles.fontWeight, '400');
        setVal('bgColorInput', styles.backgroundColor, '#ffffff');
        setVal('paddingInput', styles.padding, '40');
        setVal('marginInput', styles.margin, '0');
        setVal('btnColorInput', styles.btnColor, '#3b82f6');
        setVal('btnTextColorInput', styles.btnTextColor, '#ffffff');
        setVal('btnRadiusInput', styles.btnRadius, '6');
        setVal('btnSizeSelect', styles.btnSize, 'medium');

        // Content inputs
        setVal('sectionNameInput', section.title);
        setVal('sectionDescInput', section.description);
        // Button text might be inside content or separate
        setVal('buttonLabelInput', section.buttonText || 'Get Started');
    }


    setupStateSync() {
        // Listen for state changes from sitemap
        if (window.stateManager && typeof window.stateManager.addEventListener === 'function') {
            window.stateManager.addEventListener('section:added', (data) => {
                this.onSectionAdded(data);
            });

            window.stateManager.addEventListener('section:updated', (data) => {
                this.onSectionUpdated(data);
            });

            window.stateManager.addEventListener('section:deleted', (data) => {
                this.onSectionDeleted(data);
            });

            window.stateManager.addEventListener('sitemap:updated', (sitemap) => {
                this.onSitemapUpdated(sitemap);
            });
        }
    }

    // Toggle edit mode
    toggleEditMode() {
        this.editMode = !this.editMode;
        const container = document.getElementById('wireframeContainer');
        if (container) {
            container.classList.toggle('edit-mode', this.editMode);
        }

        // Update all sections and editable-text elements
        document.querySelectorAll('.wireframe-section').forEach(section => {
            section.classList.toggle('edit-mode', this.editMode);
        });

        document.querySelectorAll('.editable-text').forEach(el => {
            el.contentEditable = this.editMode;
        });
    }

    // Render all pages side-by-side
    renderAllPages(sitemap) {
        console.log('🎨 renderAllPages called with sitemap:', sitemap);
        const board = document.getElementById('wireframeBoard');
        if (!board) {
            console.error('❌ wireframeBoard element not found!');
            return;
        }

        console.log('✅ wireframeBoard element found');

        board.innerHTML = ''; // Clear existing

        if (sitemap && sitemap.pages && sitemap.pages.length > 0) {
            const flatPages = this.flattenPagesWithPath(sitemap.pages);
            console.log(`📄 Rendering ${flatPages.length} pages...`);
            flatPages.forEach((item, index) => {
                console.log(`  - Rendering page ${index + 1}: ${item.page.name}`);
                const column = this.createPageColumn(item.page, item.path);
                board.appendChild(column);
            });
            console.log('✅ All pages rendered successfully');
        } else {
            console.warn('⚠️ No pages found in sitemap');
            board.innerHTML = `
                <div class="empty-wireframe">
                    <h3>No pages found</h3>
                    <p>Create pages in the Sitemap view to see them here.</p>
                    <a href="index.html" class="btn btn-primary" style="margin-top: 20px; display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 8px;">Go to Sitemap</a>
                </div>
             `;
        }
    }

    flattenPagesWithPath(pages, parentPath = '') {
        const result = [];
        pages.forEach(page => {
            const path = parentPath ? `${parentPath} > ${page.name}` : page.name;
            result.push({ page, path });
            if (page.children && page.children.length > 0) {
                result.push(...this.flattenPagesWithPath(page.children, path));
            }
        });
        return result;
    }

    createPageColumn(page, pagePath = '') {
        const column = document.createElement('div');
        column.className = 'wireframe-page-column';
        column.dataset.pageId = page.id;

        // Add click handler for page selection (for export)
        column.addEventListener('click', (e) => {
            // Only select if clicking on the column itself or header, not on sections
            if (e.target.closest('.wireframe-section')) {
                return; // Let section clicks be handled by section handlers
            }

            if (window.app && typeof window.app.selectPageForExport === 'function') {
                window.app.selectPageForExport(page);
            }
        });

        // Header
        const header = document.createElement('div');
        header.className = 'page-column-header';
        header.innerHTML = `
            <h3 class="page-column-title">${page.name}</h3>
            ${pagePath ? `<div class="page-column-path">${pagePath}</div>` : ''}
        `;
        column.appendChild(header);

        // Content Container
        const content = document.createElement('div');
        content.className = 'page-column-content';

        // Sections
        if (page.sections && page.sections.length > 0) {
            page.sections.forEach((section, index) => {
                const sectionElement = this.createEditableSection(section, index, page.id);
                content.appendChild(sectionElement);
            });
        } else {
            // Empty state for column
            const empty = document.createElement('div');
            empty.className = 'column-empty-state';
            empty.innerHTML = `
                <div style="padding: 24px; text-align: center; color: #94a3b8; border: 2px dashed #e2e8f0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px;">No sections</p>
                </div>
             `;
            content.appendChild(empty);
        }

        column.appendChild(content);
        return column;
    }

    refreshPageColumn(pageId) {
        const column = document.querySelector(`.wireframe-page-column[data-page-id="${pageId}"]`);
        if (column && window.stateManager) {
            const page = window.stateManager.findPageById(pageId);
            if (page) {
                const newColumn = this.createPageColumn(page);
                column.replaceWith(newColumn);
            }
        } else if (!column && window.stateManager) {
            // New page added? Re-render all might be safer or append new column
            // For now, let's just re-render all if we can't find the column
            const sitemap = window.stateManager.getState();
            this.renderAllPages(sitemap);
        }
    }

    // Deprecated but kept for compatibility/redirect
    renderWireframe(pageId) {
        this.refreshPageColumn(pageId);
    }
    // Create editable section element
    createEditableSection(section, index, pageId) {
        const sectionEl = document.createElement('div');
        // Ensure type is lowercase for CSS matching
        const sectionType = (section.type || 'generic').toLowerCase();
        sectionEl.className = `wireframe-section ${sectionType} ${this.editMode ? 'edit-mode' : ''}`;
        sectionEl.dataset.sectionIndex = index;
        sectionEl.dataset.pageId = pageId;

        // Apply saved styles if they exist
        if (section.styles) {
            this.applyStylesToElement(sectionEl, section.styles);
        }

        // Set contentEditable state
        sectionEl.querySelectorAll('.editable-text').forEach(el => {
            el.contentEditable = this.editMode;
        });

        // Section controls
        const controls = document.createElement('div');
        controls.className = 'section-toolbar';
        controls.innerHTML = `
            <span class="section-label">Section</span>
            <button class="toolbar-btn section-btn" title="Section Options">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="4" y="4" width="6" height="6"></rect>
                    <rect x="14" y="4" width="6" height="6"></rect>
                    <rect x="4" y="14" width="6" height="6"></rect>
                </svg>
            </button>
            <button class="toolbar-btn btn-danger delete-btn" title="Delete Section">×</button>
        `;

        // Section content
        const content = this.createSectionContent(section, index, pageId);



        sectionEl.appendChild(controls);
        // Badge removed
        sectionEl.appendChild(content);



        // Bind events
        this.bindSectionEvents(sectionEl, section, index, pageId);

        return sectionEl;
    }

    applyStylesToElement(element, styles) {
        if (!styles) return;

        // Apply Section-Level Overrides (CSS Variables)
        const s = element.style;

        // Background Properties: NEVER apply scraped background to individual sections as inline style.
        // Background is controlled GLOBALLY via --global-section-bg on :root only.
        // Always clear any previously-set inline background styles to let the CSS class rule through.
        s.removeProperty('background');
        s.removeProperty('background-color');
        s.removeProperty('background-image');
        s.removeProperty('--global-section-bg');

        // Text Colors
        if (styles.textColor) s.setProperty('--wfe-text-color', styles.textColor);
        if (styles.btnColor) s.setProperty('--wfe-btn-bg', styles.btnColor);
        if (styles.btnTextColor) s.setProperty('--wfe-btn-text', styles.btnTextColor);

        // Fonts
        if (styles.headingFont) s.setProperty('--wfe-font-heading', styles.headingFont);
        if (styles.paragraphFont) s.setProperty('--wfe-font-body', styles.paragraphFont);

        // Layout (Direct properties as these aren't global variables usually)
        if (styles.padding) s.padding = `${styles.padding}px`;
        if (styles.margin) s.marginBottom = `${styles.margin}px`;
        if (styles.fontSize) s.fontSize = `${styles.fontSize}px`;
        if (styles.fontWeight) s.fontWeight = styles.fontWeight;

        // Ensure inner wrappers don't block background
        const wrapTargets = element.querySelectorAll('.wireframe-element, .hero-wireframe, .features-wireframe, .generic-wireframe, .navbar-wireframe, .hero-image .image-placeholder');
        wrapTargets.forEach(wrap => {
            // Reset direct styles that might interfere
            wrap.style.backgroundColor = '';
            wrap.style.color = '';
            wrap.style.fontFamily = '';
        });

        // Layout class toggle
        if (styles.layout) {
            const contentDiv = element.querySelector('.wireframe-element') || element.querySelector('.section-content > div');
            if (contentDiv) {
                const isAlt = styles.layout === 'alt';
                contentDiv.classList.toggle('layout-alt', isAlt);
            }
        }
    }

    // Create section content based on type
    createSectionContent(section, index, pageId) {
        const content = document.createElement('div');
        content.className = 'section-content';

        // Pass context to section object for syncing
        section.pageId = pageId;
        section.index = index;

        const type = (section.type || '').toLowerCase();
        const title = (section.title || '').toLowerCase();
        const variant = section.layoutVariant || 'layout-default';

        // Routing based on type OR title
        if (type === 'hero' || title.includes('hero')) {
            content.innerHTML = this.createHeroContent(section);
        } else if (type === 'navbar' || title.includes('nav') || title.includes('logo')) {
            content.innerHTML = this.createNavbarContent(section);
        } else if (type === 'features' || title.includes('features')) {
            content.innerHTML = this.createFeaturesContent(section);
        } else if (this.isTravelSection(type, title)) {
            content.innerHTML = this.createTravelWireframe(section, type);
        } else if (type === 'main-info' || title.includes('main info')) {
            content.innerHTML = this.createMainInfoWireframe(section, variant);
        } else if (type === 'supporting-info' || title.includes('supporting')) {
            content.innerHTML = this.createSupportingInfoWireframe(section, variant);
        } else if (type === 'testimonial' || title.includes('testimonial')) {
            content.innerHTML = this.createTestimonialWireframe(section, variant);
        } else if (type === 'footer' || title.includes('footer')) {
            content.innerHTML = this.createFooterWireframe(section, variant);
        } else {
            content.innerHTML = this.createGenericContent(section);
        }

        return content;
    }

    isTravelSection(type, title) {
        const travelTypes = [
            'search-form', 'filters', 'promo', 'results', 'sorting',
            'fare-details', 'seat-selection', 'passenger-form', 'special-requests',
            'addons', 'pricing', 'order-summary', 'gst', 'payment', 'terms', 'policies',
            'offers', 'trust', 'trip-types', 'auth', 'stats', 'management', 'support', 'summary'
        ];
        if (travelTypes.includes(type)) return true;
        const t = title || '';
        return /flight|booking|fare|seat|passenger|checkout|gst|payment|offer|pnr|trip/i.test(t);
    }

    createTravelWireframe(section, type) {
        const title = section.title || 'Section';
        const desc = section.description || '';

        const cardGrid = (items = 3) => {
            const cards = Array.from({ length: items }).map((_, i) => `
                <div style="padding: 16px; border: 1px solid #e2e8f0; border-radius: 10px; background: white;">
                    <div style="height: 8px; width: 60%; background: #e2e8f0; border-radius: 4px; margin-bottom: 10px;"></div>
                    <div style="height: 6px; width: 90%; background: #f1f5f9; border-radius: 4px;"></div>
                </div>
            `).join('');
            return `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">${cards}</div>`;
        };

        switch (type) {
            case 'search-form':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px;">
                            <div style="height: 44px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; border-radius: 8px; background: #0f172a;"></div>
                        </div>
                        <p class="editable-text" data-field="description" style="margin-top: 12px;">${desc}</p>
                    </div>
                `;
            case 'filters':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px;">
                            <span style="padding: 8px 12px; border-radius: 999px; background: #e2e8f0;">Non-stop</span>
                            <span style="padding: 8px 12px; border-radius: 999px; background: #e2e8f0;">Morning</span>
                            <span style="padding: 8px 12px; border-radius: 999px; background: #e2e8f0;">Price</span>
                            <span style="padding: 8px 12px; border-radius: 999px; background: #e2e8f0;">Airlines</span>
                        </div>
                    </div>
                `;
            case 'promo':
                return `
                    <div class="wireframe-element" style="padding: 24px; border: 2px dashed #e2e8f0; border-radius: 12px;">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <p class="editable-text" data-field="description">${desc || 'Promo banner with coupon code'}</p>
                    </div>
                `;
            case 'results':
            case 'sorting':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; gap: 12px; margin-top: 12px;">
                            ${[1,2,3].map(() => `
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 120px; gap: 12px; padding: 12px; border: 1px solid #e2e8f0; border-radius: 10px; background: white;">
                                    <div style="height: 10px; background: #e2e8f0; border-radius: 6px;"></div>
                                    <div style="height: 10px; background: #e2e8f0; border-radius: 6px;"></div>
                                    <div style="height: 10px; background: #e2e8f0; border-radius: 6px;"></div>
                                    <div style="height: 32px; background: #0f172a; border-radius: 8px;"></div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            case 'fare-details':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-top: 12px;">
                            <div style="height: 120px; border: 1px solid #e2e8f0; border-radius: 10px;"></div>
                            <div style="height: 120px; border: 1px solid #e2e8f0; border-radius: 10px;"></div>
                        </div>
                    </div>
                `;
            case 'seat-selection':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; margin-top: 12px;">
                            ${Array.from({ length: 36 }).map(() => `<div style="height: 18px; background: #e2e8f0; border-radius: 4px;"></div>`).join('')}
                        </div>
                    </div>
                `;
            case 'passenger-form':
            case 'special-requests':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px;">
                            ${Array.from({ length: 4 }).map(() => `<div style="height: 40px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>`).join('')}
                        </div>
                    </div>
                `;
            case 'addons':
            case 'pricing':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        ${cardGrid(3)}
                        <p class="editable-text" data-field="description" style="margin-top: 8px;">${desc}</p>
                    </div>
                `;
            case 'order-summary':
            case 'summary':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; gap: 8px; margin-top: 12px;">
                            ${Array.from({ length: 5 }).map(() => `<div style="height: 12px; background: #e2e8f0; border-radius: 6px;"></div>`).join('')}
                        </div>
                    </div>
                `;
            case 'gst':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px;">
                            ${Array.from({ length: 3 }).map(() => `<div style="height: 40px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>`).join('')}
                        </div>
                    </div>
                `;
            case 'payment':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: flex; gap: 12px; margin-top: 12px;">
                            <div style="flex: 1; height: 56px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="flex: 1; height: 56px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="flex: 1; height: 56px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                        </div>
                    </div>
                `;
            case 'terms':
            case 'policies':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="height: 80px; border: 1px dashed #e2e8f0; border-radius: 10px; margin-top: 12px;"></div>
                    </div>
                `;
            case 'offers':
            case 'trust':
            case 'trip-types':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        ${cardGrid(3)}
                        <p class="editable-text" data-field="description" style="margin-top: 8px;">${desc}</p>
                    </div>
                `;
            case 'auth':
                return `
                    <div class="wireframe-element" style="max-width: 460px; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: white;">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; gap: 10px; margin-top: 12px;">
                            <div style="height: 40px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 40px; border: 1px solid #e2e8f0; border-radius: 8px;"></div>
                            <div style="height: 44px; background: #0f172a; border-radius: 8px;"></div>
                        </div>
                    </div>
                `;
            case 'stats':
            case 'management':
            case 'support':
                return `
                    <div class="wireframe-element">
                        <h3 class="editable-text" data-field="title">${title}</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px;">
                            ${Array.from({ length: 3 }).map(() => `<div style="height: 70px; border: 1px solid #e2e8f0; border-radius: 10px;"></div>`).join('')}
                        </div>
                    </div>
                `;
            default:
                return this.createGenericContent(section);
        }
    }

    // Hero section template
    createHeroContent(section) {
        const variant = section.layoutVariant || 'layout-split-right';
        // this.ensureHeroContent(section); // Removed: Method missing and redundant
        const displayContent = this.generateHeroDisplayContent(section);

        // Handle all layout variants
        switch (variant) {
            case 'layout-centered':
            case 'centered':
                return `
                    <div class="hero-wireframe layout-centered">
                        <div class="hero-text" style="text-align: center; max-width: 600px; margin: 0 auto;">
                            ${displayContent}
                        </div>
                        <div class="hero-image-full" style="margin-top: 24px;">
                            <div class="image-placeholder">Hero Mockup</div>
                        </div>
                    </div>
                `;

            case 'layout-split-left':
            case 'split-left':
                return `
                    <div class="hero-wireframe layout-split-left" style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center;">
                        <div class="hero-image">
                            <div class="image-placeholder">Hero Mockup</div>
                        </div>
                        <div class="hero-text">
                            ${displayContent}
                        </div>
                    </div>
                `;

            case 'layout-full-bg':
                return `
                    <div class="hero-wireframe layout-full-bg" style="position: relative; min-height: 400px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(168,85,247,0.1));">
                        <div class="hero-text" style="text-align: center; max-width: 600px; z-index: 2;">
                            ${displayContent}
                        </div>
                    </div>
                `;

            case 'layout-asymmetric':
                return `
                    <div class="hero-wireframe layout-asymmetric" style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 32px; align-items: center;">
                        <div class="hero-text">
                            ${displayContent}
                        </div>
                        <div class="hero-image">
                            <div class="image-placeholder" style="transform: rotate(-3deg);">Hero Mockup</div>
                        </div>
                    </div>
                `;

            case 'layout-minimal':
                return `
                    <div class="hero-wireframe layout-minimal" style="padding: 60px 0;">
                        <div class="hero-text" style="max-width: 500px;">
                            ${displayContent}
                        </div>
                    </div>
                `;

            case 'layout-bold-text':
                return `
                    <div class="hero-wireframe layout-bold-text" style="text-align: center; padding: 80px 0;">
                        <div class="hero-text" style="max-width: 800px; margin: 0 auto;">
                            ${displayContent.replace('<h1', '<h1 style="font-size: 48px; font-weight: 800; line-height: 1.1;"')}
                        </div>
                    </div>
                `;

            case 'layout-video-bg':
                return `
                    <div class="hero-wireframe layout-video-bg" style="position: relative; min-height: 450px; display: flex; align-items: center; background: #1a1a1a;">
                        <div class="hero-text" style="max-width: 600px; color: white; z-index: 2;">
                            ${displayContent}
                        </div>
                        <div style="position: absolute; top: 50%; right: 40px; width: 200px; height: 150px; background: #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666;">▶ Video</div>
                    </div>
                `;

            case 'layout-diagonal':
                return `
                    <div class="hero-wireframe layout-diagonal" style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center; position: relative;">
                        <div class="hero-text">
                            ${displayContent}
                        </div>
                        <div class="hero-image" style="clip-path: polygon(10% 0, 100% 0, 100% 100%, 0 100%);">
                            <div class="image-placeholder">Hero Mockup</div>
                        </div>
                    </div>
                `;

            case 'layout-stacked':
                return `
                    <div class="hero-wireframe layout-stacked" style="display: flex; flex-direction: column; gap: 32px; align-items: center; text-align: center;">
                        <div class="hero-text" style="max-width: 600px;">
                            ${displayContent}
                        </div>
                        <div class="hero-image" style="width: 100%; max-width: 700px;">
                            <div class="image-placeholder">Hero Mockup</div>
                        </div>
                    </div>
                `;

            case 'layout-split-right':
            default:
                return `
                    <div class="hero-wireframe layout-split-right" style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center;">
                        <div class="hero-text">
                            ${displayContent}
                        </div>
                        <div class="hero-image">
                            <div class="image-placeholder">Hero Mockup</div>
                        </div>
                    </div>
                `;
        }
    }

    generateHeroDisplayContent(section) {
        let displayTitle = section.title || 'Build a stronger digital presence';
        let displayDesc = section.description || 'Professional messaging and a clear value proposition will appear here once this section is generated.';
        let displayBtn = section.buttonText || 'Explore More';

        return `
            <h1 class="editable-text" data-field="title">${displayTitle}</h1>
            <p class="editable-text" data-field="description">${displayDesc}</p>
            <button class="cta-button">${displayBtn}</button>
        `;
    }

    // Navbar section template
    createNavbarContent(section) {
        if (!section.title || section.title.toLowerCase() === 'navbar' || section.title.toLowerCase() === 'navigation bar') {
            // Default title if missing, but DO NOT hardcode "Servies"
            if (!section.title) section.title = 'Brand';
        }
        const rawTitle = (section.title || '').trim();
        const safeTitle = rawTitle || 'Logo';
        const logoContent = section.logoUrl
            ? `<img src="${section.logoUrl}" style="max-height: 40px;" alt="Logo">`
            : `<span class="editable-text" data-field="title">${safeTitle}</span>`;

        const variant = section.layoutVariant || 'layout-horizontal';
        if (!Array.isArray(section.menuItems) || section.menuItems.length === 0) {
            section.menuItems = ['Home', 'About', 'Services', 'Contact'];
        }
        const navLinks = section.menuItems.map(item => `<span class="nav-link">${item}</span>`).join('');
        const primaryAction = section.buttonText || 'Sign In';

        // Handle all layout variants
        switch (variant) {
            case 'layout-centered-logo':
                return `
                    <div class="navbar-wireframe layout-centered-logo" style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 24px;">
                        <div class="nav-links" style="display: flex; gap: 16px; justify-content: flex-end;">
                            <span class="nav-link">Home</span>
                            <span class="nav-link">About</span>
                        </div>
                        <div class="nav-logo" style="text-align: center;">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px;">
                            <span class="nav-link">Services</span>
                            <span class="nav-link">Contact</span>
                        </div>
                    </div>
                `;

            case 'layout-minimal':
                return `
                    <div class="navbar-wireframe layout-minimal" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 24px; font-size: 14px;">
                            ${navLinks}
                        </div>
                    </div>
                `;

            case 'layout-mega':
                return `
                    <div class="navbar-wireframe layout-mega" style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px; position: relative;">
                            <span class="nav-link" style="font-weight: 600;">Products ▾</span>
                            <span class="nav-link">Solutions</span>
                            <span class="nav-link">Resources</span>
                            <span class="nav-link">Contact</span>
                        </div>
                    </div>
                `;

            case 'layout-sidebar':
                return `
                    <div class="navbar-wireframe layout-sidebar" style="display: flex; flex-direction: column; gap: 16px; padding: 24px 16px;">
                        <div class="nav-logo" style="margin-bottom: 16px;">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; flex-direction: column; gap: 12px;">
                            ${navLinks}
                        </div>
                    </div>
                `;

            case 'layout-split':
                return `
                    <div class="navbar-wireframe layout-split" style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div style="display: flex; gap: 16px; align-items: center;">
                            <div class="nav-links" style="display: flex; gap: 16px;">
                                ${navLinks}
                            </div>
                            <button style="padding: 8px 16px; background: #6366f1; color: white; border: none; border-radius: 6px; cursor: pointer;">${primaryAction}</button>
                        </div>
                    </div>
                `;

            case 'layout-transparent':
                return `
                    <div class="navbar-wireframe layout-transparent" style="display: flex; justify-content: space-between; align-items: center; background: transparent; padding: 16px 0;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px;">
                            ${navLinks}
                        </div>
                    </div>
                `;

            case 'layout-sticky':
                return `
                    <div class="navbar-wireframe layout-sticky" style="display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 12px 0; background: white;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px;">
                            ${navLinks}
                        </div>
                    </div>
                `;

            case 'layout-hamburger':
                return `
                    <div class="navbar-wireframe layout-hamburger" style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div style="font-size: 24px; cursor: pointer;">☰</div>
                    </div>
                `;

            case 'layout-full-width':
                return `
                    <div class="navbar-wireframe layout-full-width" style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 16px 24px; margin: -16px; margin-bottom: 16px;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px;">
                            ${navLinks}
                        </div>
                    </div>
                `;

            case 'layout-horizontal':
            default:
                return `
                    <div class="navbar-wireframe layout-horizontal" style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="nav-logo">
                            ${logoContent}
                        </div>
                        <div class="nav-links" style="display: flex; gap: 16px;">
                            ${navLinks}
                        </div>
                    </div>
                `;
        }
    }

    // Features section template
    createFeaturesContent(section) {
        const variant = section.layoutVariant || 'layout-grid-3';
        const features = this.generateFeaturesList(section, variant);
        const intro = section.description
            ? `<p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;max-width:720px;margin:12px auto 0;">${section.description}</p>`
            : '';

        // Handle all layout variants
        switch (variant) {
            case 'layout-grid-2':
                return `
                    <div class="features-wireframe layout-grid-2">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        ${intro}
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-grid-4':
                return `
                    <div class="features-wireframe layout-grid-4">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        ${intro}
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-horizontal':
                return `
                    <div class="features-wireframe layout-horizontal">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        ${intro}
                        <div class="features-grid" style="display: flex; gap: 24px; overflow-x: auto; margin-top: 24px; padding-bottom: 16px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-staggered':
                return `
                    <div class="features-wireframe layout-staggered">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        ${intro}
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 24px;">
                            ${features.split('</div>').map((f, i) => i % 2 === 1 ? `${f}</div>` : `<div style="margin-top: ${i * 20}px;">${f}</div>`).join('')}
                        </div>
                    </div>
                `;

            case 'layout-masonry':
                return `
                    <div class="features-wireframe layout-masonry">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        ${intro}
                        <div class="features-grid" style="column-count: 3; column-gap: 24px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-list':
                return `
                    <div class="features-wireframe layout-list">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        <div class="features-grid" style="display: flex; flex-direction: column; gap: 16px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-bento':
                return `
                    <div class="features-wireframe layout-bento">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: 150px; gap: 16px; margin-top: 24px;">
                            ${features.split('</div>').map((f, i) => {
                    const span = i === 0 ? 'grid-column: span 2; grid-row: span 2;' : '';
                    return `<div style="${span}">${f}</div>`;
                }).join('')}
                        </div>
                    </div>
                `;

            case 'layout-carousel':
                return `
                    <div class="features-wireframe layout-carousel">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        <div class="features-grid" style="display: flex; gap: 24px; overflow-x: auto; scroll-snap-type: x mandatory; margin-top: 24px;">
                            ${features}
                        </div>
                        <div style="text-align: center; margin-top: 16px; color: #94a3b8;">◀ ● ● ● ▶</div>
                    </div>
                `;

            case 'layout-tabs':
                return `
                    <div class="features-wireframe layout-tabs">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        <div style="display: flex; gap: 16px; margin-top: 24px; border-bottom: 2px solid #e2e8f0;">
                            <div style="padding: 12px 24px; border-bottom: 2px solid #6366f1; margin-bottom: -2px; font-weight: 600;">Tab 1</div>
                            <div style="padding: 12px 24px; color: #94a3b8;">Tab 2</div>
                            <div style="padding: 12px 24px; color: #94a3b8;">Tab 3</div>
                        </div>
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;

            case 'layout-grid-3':
            default:
                return `
                    <div class="features-wireframe layout-grid-3">
                        <h2 class="editable-text" data-field="title">${section.title || 'Features'}</h2>
                        <div class="features-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 24px;">
                            ${features}
                        </div>
                    </div>
                `;
        }
    }

    generateFeaturesList(section) {
        // Standardize items storage
        if (!Array.isArray(section.items) || section.items.length === 0) {
            section.items = [
                { icon: this.getSectionFallbackVisual('features', 0).emoji, title: 'Fast Performance', desc: 'Optimized for speed and efficiency.' },
                { icon: this.getSectionFallbackVisual('features', 1).emoji, title: 'Secure Platform', desc: 'Enterprise-grade security protection.' },
                { icon: this.getSectionFallbackVisual('features', 2).emoji, title: 'Easy to Use', desc: 'Intuitive interface for better experience.' }
            ];
            // Ensure state is updated with these defaults
            this.syncSectionData(section);
        }

        return section.items.map((f, i) => `
            <div class="feature-item" data-item-index="${i}">
                <div class="feature-icon">${f.icon || this.getSectionFallbackVisual('features', i).emoji}</div>
                <h3 class="editable-text" data-field="item-title" data-index="${i}">${f.title || `Feature ${i + 1}`}</h3>
                <p class="editable-text" data-field="item-desc" data-index="${i}">${f.desc || f.description || 'Feature description'}</p>
            </div>
         `).join('');
    }

    syncSectionData(section) {
        if (window.stateManager && section.pageId !== undefined && section.index !== undefined) {
            window.stateManager.updateSection(section.pageId, section.index, section);
            console.log(`✅ Synced section ${section.index} for page ${section.pageId}`);
        }
    }

    // Generic content template - handles all other section types
    createGenericContent(section) {
        const variant = section.layoutVariant || 'layout-default';
        const sectionType = this.detectResolvedSectionType(section);

        // For generic sections, create a flexible layout based on variant
        const content = this.generateGenericDisplayContent(section);

        // Check if type is one of the specialized ones that handles its own layout
        const specializedTypes = [
            'testimonial', 'footer', 'about', 'contact', 'pricing', 'gallery', 'blog', 'stats', 'cta',
            'services', 'service', 'story', 'team', 'culture', 'values', 'location', 'map',
            'contact-details', 'main-info', 'main-information', 'supporting-info', 'supporting-information',
            'contact-form', 'form', 'key-features', 'features', 'information', 'info'
        ];

        // If specialized, don't apply the generic layout wrapper styles
        const isSpecialized = specializedTypes.includes(sectionType);
        const wrapperVariant = isSpecialized ? 'layout-default' : variant;
        const wrapperStyle = isSpecialized ? '' : this.getGenericLayoutStyles(variant, sectionType);

        // Determine title alignment based on layout
        let titleStyle = '';
        if (variant === 'layout-grid-4' || variant === 'layout-grid-3' || variant === 'layout-grid-2') {
            titleStyle = 'text-align: center; margin-bottom: 24px; width: 100%;';
        }

        // For Split Layout, suppress the outer title (it will be rendered inside the content)
        // DEBUG: Check what the variant actually IS
        console.log('DEBUG: Rendering generic content. Variant:', variant, 'Section:', sectionType);

        let titleHtml = `
            <h2 class="editable-text" data-field="title" style="${titleStyle}">${section.title || this.getDefaultTitle(sectionType)}</h2>`;

        if (variant === 'layout-split') {
            console.log('DEBUG: Suppressing outer title for split layout');
            titleHtml = '';
        }

        return `
            <div class="generic-wireframe ${wrapperVariant}" style="${wrapperStyle}">
                ${titleHtml}
                <div class="content-placeholder-text">
                    ${content}
                </div>
            </div>
        `;
    }

    getDefaultTitle(sectionType) {
        const titles = {
            testimonial: 'What Our Clients Say',
            footer: 'Footer',
            about: 'About Us',
            contact: 'Get In Touch',
            pricing: 'Pricing Plans',
            gallery: 'Our Work',
            blog: 'Latest Posts',
            stats: 'Our Impact',
            cta: 'Ready to Get Started?'
        };
        return titles[sectionType] || 'Section Title';
    }

    getGenericLayoutStyles(variant, sectionType) {
        // Return inline styles based on layout variant
        const styles = {
            'layout-centered': 'text-align: center; max-width: 600px; margin: 0 auto;',
            'layout-split': 'display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center;',
            'layout-grid-3': 'display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;',
            'layout-grid-2': 'display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;',
            'layout-grid-4': 'display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;',
            'layout-horizontal': 'display: flex; gap: 24px; overflow-x: auto;',
            'layout-list': 'display: flex; flex-direction: column; gap: 16px;',
            'layout-masonry': 'column-count: 3; column-gap: 24px;',
            'layout-minimal': 'padding: 40px 0;',
            'layout-banner': 'background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 48px; border-radius: 12px; text-align: center;',
            'layout-card': 'background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);',
            'layout-featured': 'text-align: center; padding: 60px 0;',
            'layout-timeline': 'position: relative; padding-left: 40px; border-left: 3px solid #6366f1;',
            'layout-stacked': 'display: flex; flex-direction: column; gap: 24px;',
            'layout-carousel': 'display: flex; gap: 24px; overflow-x: auto; scroll-snap-type: x mandatory;'
        };
        return styles[variant] || '';
    }

    detectResolvedSectionType(section) {
        let sectionType = section.type || 'generic';
        const title = (section.title || '').toLowerCase();

        // Fallback: Detect section type from title if type is 'content' or 'generic' or 'info'
        if (sectionType === 'content' || sectionType === 'generic' || sectionType === 'info') {
            if (title.includes('service') || title.includes('offering')) {
                return 'services';
            } else if (title.includes('story') || title.includes('history') || title.includes('journey')) {
                return 'story';
            } else if (title.includes('team') || title.includes('staff') || title.includes('people')) {
                return 'team';
            } else if (title.includes('culture') || title.includes('value')) {
                return 'culture';
            } else if (title.includes('location') || title.includes('map') || title.includes('address')) {
                return 'location';
            } else if (title.includes('contact form')) {
                return 'contact-form';
            } else if (title.includes('contact detail') || title.includes('contact info')) {
                return 'contact-details';
            } else if (title.includes('main information')) {
                return 'main-info';
            } else if (title.includes('supporting content') || title.includes('supporting information')) {
                return 'supporting-info';
            } else if (title.includes('information') || title.includes('detail')) {
                return 'information';
            }
        }
        return sectionType;
    }

    generateGenericDisplayContent(section) {
        const sectionType = this.detectResolvedSectionType(section);
        const variant = section.layoutVariant || 'layout-default';

        // Create specific wireframe content based on section type
        switch (sectionType) {
            case 'testimonial':
                return this.createTestimonialWireframe(section, variant);
            case 'footer':
                return this.createFooterWireframe(section, variant);
            case 'about':
                return this.createAboutWireframe(section, variant);
            case 'contact':
                return this.createContactWireframe(section, variant);
            case 'pricing':
                return this.createPricingWireframe(section, variant);
            case 'gallery':
                return this.createGalleryWireframe(section, variant);
            case 'blog':
                return this.createBlogWireframe(section, variant);
            case 'stats':
                return this.createStatsWireframe(section, variant);
            case 'cta':
                return this.createCTAWireframe(section, variant);
            case 'services':
            case 'service':
                return this.createServicesWireframe(section, variant);
            case 'story':
                return this.createStoryWireframe(section, variant);
            case 'team':
                return this.createTeamWireframe(section, variant);
            case 'culture':
            case 'values':
                return this.createCultureWireframe(section, variant);
            case 'location':
            case 'map':
                return this.createLocationWireframe(section, variant);
            case 'contact-details':
                return this.createContactDetailsWireframe(section, variant);
            case 'main-info':
            case 'main-information':
                return this.createMainInfoWireframe(section, variant);
            case 'supporting-info':
            case 'supporting-information':
                return this.createSupportingInfoWireframe(section, variant);
            case 'contact-form':
            case 'form':
                return this.createContactFormWireframe(section, variant);
            case 'key-features':
            case 'features':
                return this.createKeyFeaturesWireframe(section, variant);
            case 'information':
            case 'info':
                return this.createInformationWireframe(section, variant);
            default:
                // Generate intelligent wireframe based on section description and type
                return this.generateIntelligentWireframe(section, sectionType);
        }
    }

    generateIntelligentWireframe(section, sectionType) {
        const desc = section.description || '';
        const title = section.title || 'Section Content';
        const items = Array.isArray(section.items) ? section.items.filter(Boolean) : [];
        const buttonText = section.buttonText || 'Learn More';

        if (items.length > 0) {
            const columns = items.length >= 3 ? 3 : items.length === 2 ? 2 : 1;
            return `
                <div style="max-width: 960px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 32px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 34px; font-weight: 700; margin-bottom: 14px; color: #1e293b;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 17px; color: #64748b; line-height: 1.7; max-width: 720px; margin: 0 auto;">${desc}</p>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(${columns}, 1fr); gap: 24px; margin-top: 24px;">
                        ${items.map((item, i) => `
                            <div style="padding: 24px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                                <div style="font-size: 32px; margin-bottom: 14px; color: #475569;">${item.icon || '+'}</div>
                                <h3 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 20px; font-weight: 600; margin-bottom: 10px; color: #1e293b;">${item.title || item.label || `Item ${i + 1}`}</h3>
                                <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 14px; color: #64748b; line-height: 1.7;">${item.desc || item.description || item.value || ''}</p>
                                ${item.features && item.features.length ? `
                                    <div style="display: grid; gap: 8px; margin-top: 16px;">
                                        ${item.features.map(feature => `<div style="font-size: 13px; color: #475569;">• ${feature}</div>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Parse description for key information
        const hasContact = desc.toLowerCase().includes('contact') || desc.toLowerCase().includes('phone') || desc.toLowerCase().includes('email');
        const hasLocation = desc.toLowerCase().includes('location') || desc.toLowerCase().includes('map') || desc.toLowerCase().includes('address');
        const hasTeam = desc.toLowerCase().includes('team') || desc.toLowerCase().includes('member') || desc.toLowerCase().includes('staff');
        const hasServices = desc.toLowerCase().includes('service') || desc.toLowerCase().includes('offering');
        const hasFeatures = desc.toLowerCase().includes('feature') || desc.toLowerCase().includes('benefit');
        const hasForm = desc.toLowerCase().includes('form') || desc.toLowerCase().includes('input');
        const hasInfo = desc.toLowerCase().includes('information') || desc.toLowerCase().includes('detail');

        // Generate appropriate wireframe based on content
        if (hasContact && hasLocation) {
            // Contact details with location
            return `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 24px;">
                    <div>
                        <h3 class="editable-text" data-field="title" style="font-size: 22px; font-weight: 600; margin-bottom: 20px; color: #1e293b;">${title}</h3>
                        <p class="editable-text" data-field="description" style="font-size: 14px; color: #64748b; line-height: 1.7; margin-bottom: 20px;">${desc}</p>
                        ${['Phone', 'Email', 'Hours'].map(item => `
                            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px; padding: 16px; background: #f8fafc; border-radius: 8px;">
                                <div>
                                    <div style="font-weight: 600; font-size: 16px; color: #334155;">${item}</div>
                                    <div style="font-size: 14px; color: #64748b;">${desc || 'Contact details provided by the project brief.'}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="background: #e2e8f0; border-radius: 12px; height: 300px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 18px;">
                        ${section.mapLabel || 'Map Location'}
                    </div>
                </div>
            `;
        } else if (hasContact) {
            // Contact details only
            return `
                <div style="max-width: 700px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 24px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 30px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 16px; color: #64748b; line-height: 1.7;">${desc}</p>
                    </div>
                    ${['Phone Number', 'Email Address', 'Live Chat', 'Business Hours'].map(item => `
                        <div style="display: flex; gap: 20px; padding: 24px; margin-bottom: 16px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                            <div>
                                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #1e293b;">${item}</h3>
                                <p style="font-size: 15px; color: #64748b;">${desc || 'Project-specific contact details appear here.'}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (hasForm) {
            // Form layout
            return `
                <div style="max-width: 600px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 24px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 30px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 16px; color: #64748b; line-height: 1.7;">${desc}</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #334155;">Name</label>
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; color: #94a3b8;">Enter your name</div>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #334155;">Email</label>
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; color: #94a3b8;">Enter your email</div>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #334155;">Message</label>
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 12px 60px 12px; color: #94a3b8;">Your message here</div>
                    </div>
                    <button style="background: #3b82f6; color: white; padding: 12px 32px; border-radius: 8px; font-weight: 600; border: none; width: 100%;">${buttonText}</button>
                </div>
            `;
        } else if (hasTeam) {
            // Team members grid
            return `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 24px;">
                    ${['Team Member 1', 'Team Member 2', 'Team Member 3'].map(name => `
                        <div style="text-align: center; padding: 24px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                            <div style="width: 80px; height: 80px; border-radius: 50%; background: #cbd5e1; margin: 0 auto 16px;"></div>
                            <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #1e293b;">${name}</h3>
                            <p style="font-size: 14px; color: #64748b; margin-bottom: 12px;">Role / Position</p>
                            <p style="font-size: 13px; color: #94a3b8; line-height: 1.6;">Brief bio and expertise description</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (hasServices) {
            // Services grid
            return `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 24px;">
                    ${['🎯 Service One', '⚡ Service Two', '🚀 Service Three'].map(service => `
                        <div style="padding: 32px; background: white; border-radius: 12px; border: 2px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <div style="font-size: 48px; margin-bottom: 16px;">${service.split(' ')[0]}</div>
                            <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 12px; color: #1e293b;">${service.substring(2)}</h3>
                            <p style="font-size: 15px; color: #64748b; line-height: 1.7; margin-bottom: 16px;">Description of the service offering and key benefits provided.</p>
                            <a href="#" style="color: #3b82f6; font-weight: 600; font-size: 14px; text-decoration: none;">Learn More →</a>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (hasFeatures) {
            // Features grid
            return `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; margin-top: 24px;">
                    ${['📊 Feature One', '🔒 Feature Two', '⚡ Feature Three'].map(feature => `
                        <div style="text-align: center; padding: 24px;">
                            <div style="font-size: 56px; margin-bottom: 16px;">${feature.split(' ')[0]}</div>
                            <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 12px; color: #1e293b;">${feature.substring(2)}</h3>
                            <p style="font-size: 15px; color: #64748b; line-height: 1.7;">Key benefit and value proposition for this feature.</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (hasInfo || sectionType === 'information' || sectionType === 'main-info' || sectionType === 'supporting-info') {
            // Information cards
            return `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 24px;">
                    ${['📋 Information Block 1', '💡 Information Block 2', '📊 Information Block 3', '🔍 Information Block 4'].map(item => `
                        <div style="padding: 28px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                            <div style="font-size: 40px; margin-bottom: 16px;">${item.split(' ')[0]}</div>
                            <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 10px; color: #1e293b;">${item.substring(2)}</h3>
                            <p style="font-size: 15px; color: #64748b; line-height: 1.7;">${desc.substring(0, 100) || 'Detailed information and content for this section.'}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            // Default: Rich content layout with description
            return `
                <div style="max-width: 900px; margin: 0 auto;">
                    <div style="text-align: center; margin-bottom: 40px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 36px; font-weight: 700; margin-bottom: 16px; color: #1e293b;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 18px; color: #64748b; line-height: 1.8; max-width: 700px; margin: 0 auto;">${desc || this.getTitleAwareFallbackText(title)}</p>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 32px;">
                        ${['Overview', 'Highlights', 'Next Step'].map(point => `
                            <div style="text-align: center; padding: 24px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                                <h4 style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 8px;">${point}</h4>
                                <p style="font-size: 14px; color: #64748b; line-height: 1.6;">${desc || 'Key project information appears here.'}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }

    createTestimonialWireframe(section, variant) {
        if (!Array.isArray(section.items) || section.items.length === 0) {
            section.items = [
                { name: 'John Doe', role: 'CEO, Company', quote: 'This product changed our business completely!' },
                { name: 'Jane Smith', role: 'Marketing Director', quote: 'Excellent service and support. Highly recommended!' },
                { name: 'Mike Johnson', role: 'Founder', quote: 'Best investment we made this year.' }
            ];
            this.syncSectionData(section);
        }
        const testimonials = section.items;
        const header = `
            <div style="text-align:center;max-width:760px;margin:0 auto 28px;">
                <h2 class="editable-text" data-field="title" style="font-size:32px;font-weight:700;margin-bottom:12px;color:#1e293b;">${section.title || 'Client Testimonials'}</h2>
                <p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;">${section.description || ''}</p>
            </div>
        `;

        // Handle different layout variants
        switch (variant) {
            case 'layout-carousel':
                return `
                    ${header}
                    <div style="display: flex; gap: 24px; overflow-x: auto; scroll-snap-type: x mandatory; margin-top: 24px;">
                        ${testimonials.map((t, i) => `
                            <div style="min-width: 80%; background: #f8fafc; padding: 32px; border-radius: 12px; border: 1px solid #e2e8f0; scroll-snap-align: start;" data-item-index="${i}">
                                <div style="font-size: 32px; color: #6366f1; margin-bottom: 16px;">"</div>
                                <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 18px; font-style: italic; margin-bottom: 24px; color: #475569;">${t.quote || t.desc}</p>
                                <div style="display: flex; align-items: center; gap: 16px;">
                                    <div style="width: 50px; height: 50px; border-radius: 50%; background: #cbd5e1;"></div>
                                    <div>
                                        <div class="editable-text" data-field="item-title" data-index="${i}" style="font-weight: 600; font-size: 16px;">${t.name || t.title}</div>
                                        <div style="font-size: 14px; color: #94a3b8;">${t.role}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="text-align: center; margin-top: 16px; color: #94a3b8;">◀ ● ● ● ▶</div>
                `;

            case 'layout-featured':
                return `
                    ${header}
                    <div style="max-width: 800px; margin: 40px auto; text-align: center;">
                        <div style="font-size: 48px; color: #6366f1; margin-bottom: 24px;">"</div>
                        <p data-field="item-desc" style="font-size: 24px; font-style: italic; margin-bottom: 32px; color: #1e293b; line-height: 1.6;">${testimonials[0].quote}</p>
                        <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
                            <div style="width: 60px; height: 60px; border-radius: 50%; background: #cbd5e1;"></div>
                            <div style="text-align: left;">
                                <div data-field="item-title" style="font-weight: 700; font-size: 18px;">${testimonials[0].name}</div>
                                <div style="font-size: 14px; color: #94a3b8;">${testimonials[0].role}</div>
                            </div>
                        </div>
                    </div>
                `;

            case 'layout-masonry':
                return `
                    ${header}
                    <div style="column-count: 2; column-gap: 24px; margin-top: 24px;">
                        ${testimonials.map(t => `
                            <div style="break-inside: avoid; background: #f8fafc; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 24px;">
                                <div style="font-size: 24px; color: #6366f1; margin-bottom: 12px;">"</div>
                                <p data-field="item-desc" style="font-style: italic; margin-bottom: 16px; color: #475569;">${t.quote}</p>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #cbd5e1;"></div>
                                    <div>
                                        <div data-field="item-title" style="font-weight: 600; font-size: 14px;">${t.name}</div>
                                        <div style="font-size: 12px; color: #94a3b8;">${t.role}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-horizontal':
                return `
                    ${header}
                    <div style="display: flex; gap: 24px; overflow-x: auto; margin-top: 24px; padding-bottom: 16px;">
                        ${testimonials.map(t => `
                            <div style="min-width: 350px; background: #f8fafc; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; flex-shrink: 0;">
                                <div style="font-size: 24px; color: #6366f1; margin-bottom: 12px;">"</div>
                                <p data-field="item-desc" style="font-style: italic; margin-bottom: 16px; color: #475569;">${t.quote}</p>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #cbd5e1;"></div>
                                    <div>
                                        <div data-field="item-title" style="font-weight: 600; font-size: 14px;">${t.name}</div>
                                        <div style="font-size: 12px; color: #94a3b8;">${t.role}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-split':
                return `
                    ${header}
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: center; margin-top: 24px;">
                        <div style="height: 300px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                            Customer Video
                        </div>
                        <div>
                            <div style="font-size: 32px; color: #6366f1; margin-bottom: 16px;">"</div>
                            <p data-field="item-desc" style="font-size: 18px; font-style: italic; margin-bottom: 24px; color: #475569; line-height: 1.6;">${testimonials[0].quote}</p>
                            <div style="display: flex; align-items: center; gap: 16px;">
                                <div style="width: 50px; height: 50px; border-radius: 50%; background: #cbd5e1;"></div>
                                <div>
                                    <div data-field="item-title" style="font-weight: 600; font-size: 16px;">${testimonials[0].name}</div>
                                    <div style="font-size: 14px; color: #94a3b8;">${testimonials[0].role}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

            case 'layout-grid-3':
            default:
                return `
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 24px;">
                        ${testimonials.map(t => `
                            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <div style="font-size: 24px; color: #6366f1; margin-bottom: 12px;">"</div>
                                <p data-field="item-desc" style="font-style: italic; margin-bottom: 16px; color: #475569;">${t.quote}</p>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #cbd5e1;"></div>
                                    <div>
                                        <div data-field="item-title" style="font-weight: 600; font-size: 14px;">${t.name}</div>
                                        <div style="font-size: 12px; color: #94a3b8;">${t.role}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    createFooterWireframe(section, variant) {
        const v = (variant || 'layout-multi-column').toLowerCase();
        const footerItems = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Company', items: ['About Us', 'Careers', 'Press', 'Blog'] },
            { title: 'Product', items: ['Features', 'Pricing', 'Security', 'Updates'] },
            { title: 'Resources', items: ['Documentation', 'Guides', 'API', 'Support'] },
            { title: 'Legal', items: ['Privacy', 'Terms', 'Cookies', 'Licenses'] }
        ]).map(item => ({
            title: item.title || 'Links',
            items: Array.isArray(item.items) && item.items.length > 0
                ? item.items
                : String(item.desc || item.description || '').split(/,|\n/).map(part => part.trim()).filter(Boolean).slice(0, 4)
        }));

        let contentHtml = '';
        if (v === 'layout-centered') {
            contentHtml = `
                <div style="text-align: center; max-width: 800px; margin: 0 auto;">
                    <h5 style="font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 24px;">${section.title || 'Brand'}</h5>
                    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 32px; margin-bottom: 40px;">
                        ${footerItems.flatMap(col => col.items).slice(0, 8).map(item => `
                            <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none; transition: all 0.2s ease;">${item}</a>
                        `).join('')}
                    </div>
                </div>
            `;
        } else if (v === 'layout-minimal') {
            contentHtml = `
                <div style="display: flex; flex-direction: column; md-flex-direction: row; justify-content: space-between; align-items: center; gap: 24px;">
                    <div style="font-weight: 700; font-size: 20px;">${section.title || 'Brand'}</div>
                    <div style="display: flex; gap: 24px;">
                        <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none;">Privacy</a>
                        <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none;">Terms</a>
                        <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none;">Contact</a>
                    </div>
                </div>
            `;
        } else if (v === 'layout-newsletter') {
            contentHtml = `
                <div class="footer-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 48px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 48px; margin-bottom: 32px;">
                    <div style="grid-column: span 2;">
                        <h5 style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">Stay Updated</h5>
                        <p style="font-size: 14px; color: #64748b; margin-bottom: 24px;">${section.description || this.getTitleAwareFallbackText(section.title || 'footer', 'footer')}</p>
                        <div style="display: flex; gap: 12px; max-width: 400px;">
                            <input type="email" placeholder="Email address" style="flex: 1; padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px;">
                            <button style="background: #8b5e34; color: white; padding: 12px 24px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;">${section.buttonText || 'Join'}</button>
                        </div>
                    </div>
                    ${footerItems.slice(0, 2).map((col, i) => `
                        <div>
                            <h5 style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 24px;">${col.title}</h5>
                            <div style="display: flex; flex-direction: column; gap: 12px;">
                                ${col.items.map(item => `
                                    <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none;">${item}</a>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            // Default Multi-column
            contentHtml = `
                <div class="footer-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 48px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 48px; margin-bottom: 32px;">
                    ${footerItems.map((col, i) => `
                        <div>
                            <h5 style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 24px;">${col.title}</h5>
                            <div style="display: flex; flex-direction: column; gap: 12px;">
                                ${col.items.map(item => `
                                    <a href="#" class="footer-link" style="font-size: 14px; color: #4b5563; text-decoration: none; transition: all 0.2s ease;">${item}</a>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <div class="footer-section" style="padding: 64px 0; width: 100%; box-sizing: border-box;">
                <div style="max-width: 1280px; margin: 0 auto; padding: 0 24px; box-sizing: border-box;">
                    ${contentHtml}
                    <div style="text-align: center; margin-top: 32px;">
                        <p style="font-size: 14px; color: #6b7280;">© 2024 Company Name. All rights reserved.</p>
                    </div>
                </div>
                <style>
                    .footer-link:hover { color: #8b5e34 !important; }
                    @media (max-width: 768px) {
                        .footer-grid { grid-template-columns: 1fr !important; gap: 32px !important; }
                    }
                    @media (min-width: 640px) and (max-width: 767px) {
                        .footer-grid { grid-template-columns: repeat(2, 1fr) !important; }
                    }
                </style>
            </div>
        `;
    }

    createAboutWireframe(section, variant) {
        const stats = (Array.isArray(section.items) && section.items.length > 0 ? section.items.slice(0, 3) : [
            { title: '10+', desc: 'Years' },
            { title: '500+', desc: 'Clients' },
            { title: '50+', desc: 'Team' }
        ]);
        return `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: center; margin-top: 24px;">
                <div>
                    <p class="editable-text" data-field="description" style="margin-bottom: 16px; line-height: 1.6;">${section.description || 'We are a team of dedicated professionals committed to excellence and innovation in everything we do.'}</p>
                    <p style="margin-bottom: 16px; line-height: 1.6;">${section.subdescription || 'Our mission is to deliver exceptional value to our customers through thoughtful strategy, design, and execution.'}</p>
                    <div style="display: flex; gap: 16px; margin-top: 24px;">
                        ${stats.map((stat, i) => `
                            <div style="text-align: center;">
                                <div class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 32px; font-weight: 700; color: #6366f1;">${stat.title || ''}</div>
                                <div class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 14px; color: #64748b;">${stat.desc || ''}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div style="height: 300px; background: #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                    ${section.mediaLabel || 'Brand Story Visual'}
                </div>
            </div>
        `;
    }

    createStatsWireframe(section, variant) {
        const stats = [
            { value: '10K+', label: 'Active Users' },
            { value: '99.9%', label: 'Uptime' },
            { value: '24/7', label: 'Support' },
            { value: '50+', label: 'Countries' }
        ];

        switch (variant) {
            case 'layout-horizontal':
                return `
                    <div style="display: flex; justify-content: space-around; align-items: center; background: #f8fafc; padding: 40px; border-radius: 12px; margin-top: 24px;">
                        ${stats.map(stat => `
                            <div class="stat-item" style="text-align: center;">
                                <div data-field="item-title" style="font-size: 40px; font-weight: 800; color: #6366f1; margin-bottom: 8px;">${stat.value}</div>
                                <div data-field="item-desc" style="font-size: 14px; color: #64748b;">${stat.label}</div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-cards':
                return `
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 24px;">
                        ${stats.map(stat => `
                            <div class="stat-item" style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 24px; text-align: center;">
                                <div data-field="item-title" style="font-size: 36px; font-weight: 800; color: #6366f1; margin-bottom: 8px;">${stat.value}</div>
                                <div data-field="item-desc" style="font-size: 14px; color: #64748b;">${stat.label}</div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-minimal':
                return `
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; margin-top: 24px; max-width: 600px; margin-left: auto; margin-right: auto;">
                        ${stats.map(stat => `
                            <div class="stat-item" style="text-align: center;">
                                <div data-field="item-title" style="font-size: 56px; font-weight: 800; color: #6366f1; margin-bottom: 8px;">${stat.value}</div>
                                <div data-field="item-desc" style="font-size: 16px; color: #64748b;">${stat.label}</div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-counter':
            default:
                return `
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; margin-top: 24px; text-align: center;">
                        ${stats.map(stat => `
                            <div class="stat-item">
                                <div data-field="item-title" style="font-size: 48px; font-weight: 800; color: #6366f1; margin-bottom: 8px;">${stat.value}</div>
                                <div data-field="item-desc" style="font-size: 16px; color: #64748b;">${stat.label}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    createCTAWireframe(section, variant) {
        const title = section.title || 'Take the next step';
        const description = section.description || 'Move this visitor toward the primary conversion action.';
        const primaryButton = section.buttonText || 'Get Started';
        const secondaryButton = (Array.isArray(section.items) && section.items[0] && (section.items[0].title || section.items[0].label)) || 'Learn More';

        switch (variant) {
            case 'layout-split':
                return `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: center; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 60px; border-radius: 12px; margin-top: 24px;">
                        <div>
                            <h2 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 16px;">${title}</h2>
                            <p class="editable-text" data-field="description" style="font-size: 18px; opacity: 0.9;">${description}</p>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            <button style="padding: 14px 32px; background: white; color: #6366f1; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;">${primaryButton}</button>
                            <button style="padding: 14px 32px; background: transparent; color: white; border: 2px solid white; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;">${secondaryButton}</button>
                        </div>
                    </div>
                `;

            case 'layout-banner':
                return `
                    <div style="background: linear-gradient(90deg, #6366f1, #a855f7); color: white; padding: 32px 60px; border-radius: 12px; margin-top: 24px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 class="editable-text" data-field="title" style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">${title}</h2>
                            <p class="editable-text" data-field="description" style="font-size: 16px; opacity: 0.9;">${description}</p>
                        </div>
                        <button style="padding: 14px 32px; background: white; color: #6366f1; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer; white-space: nowrap;">${primaryButton}</button>
                    </div>
                `;

            case 'layout-minimal':
                return `
                    <div style="text-align: center; padding: 80px 40px; margin-top: 24px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 36px; font-weight: 700; margin-bottom: 16px; color: #1e293b;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 18px; margin-bottom: 32px; color: #64748b;">${description}</p>
                        <button style="padding: 14px 32px; background: #6366f1; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;">${primaryButton}</button>
                    </div>
                `;

            case 'layout-centered':
            default:
                return `
                    <div style="background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 60px; border-radius: 12px; text-align: center; margin-top: 24px;">
                        <h2 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 16px;">${title}</h2>
                        <p class="editable-text" data-field="description" style="font-size: 18px; margin-bottom: 32px; opacity: 0.9;">${description}</p>
                        <div style="display: flex; gap: 16px; justify-content: center;">
                            <button style="padding: 14px 32px; background: white; color: #6366f1; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;">${primaryButton}</button>
                            <button style="padding: 14px 32px; background: transparent; color: white; border: 2px solid white; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;">${secondaryButton}</button>
                        </div>
                    </div>
                `;
        }
    }

    createStoryWireframe(section, variant) {
        switch (variant) {
            case 'layout-timeline':
                return `
                    <div class="story-timeline" style="max-width: 800px; margin: 40px auto; width: 100%;">
                        <div style="border-left: 3px solid #6366f1; padding-left: 32px; position: relative;">
                            ${['2020', '2021', '2022', '2023'].map(year => `
                                <div style="margin-bottom: 40px; position: relative;">
                                    <div style="position: absolute; left: -41px; width: 16px; height: 16px; background: #6366f1; border-radius: 50%; border: 3px solid white;"></div>
                                    <div style="font-size: 24px; font-weight: 700; color: #6366f1; margin-bottom: 8px;">${year}</div>
                                    <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">Major Milestone</h3>
                                    <p style="color: #64748b; line-height: 1.6; word-wrap: break-word;">Achieved significant growth and expanded our services to new markets.</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-split':
                return `
                    <div class="story-split ${variant}" style="display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; margin-top: 24px; width: 100%;">
                        <div style="height: 400px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 18px; box-sizing: border-box;">
                            Company Image
                        </div>
                        <div style="box-sizing: border-box;">
                            <h2 style="font-size: 32px; font-weight: 700; margin-bottom: 20px; color: #1e293b; word-wrap: break-word;">Our Story</h2>
                            <p style="font-size: 16px; color: #64748b; line-height: 1.8; margin-bottom: 16px; word-wrap: break-word;">
                                Founded in 2020, we started with a simple mission: to make technology accessible to everyone.
                            </p>
                            <p style="font-size: 16px; color: #64748b; line-height: 1.8; margin-bottom: 16px; word-wrap: break-word;">
                                Today, we serve thousands of customers worldwide and continue to innovate every day.
                            </p>
                            <p style="font-size: 16px; color: #64748b; line-height: 1.8; word-wrap: break-word;">
                                Our commitment to excellence drives everything we do.
                            </p>
                        </div>
                    </div>
                `;

            case 'layout-centered':
            default:
                return `
                    <div class="story-centered" style="max-width: 700px; margin: 40px auto; text-align: center; width: 100%; box-sizing: border-box;">
                        <h2 style="font-size: 36px; font-weight: 700; margin-bottom: 24px; color: #1e293b; word-wrap: break-word;">Our Story</h2>
                        <p style="font-size: 18px; color: #64748b; line-height: 1.8; margin-bottom: 20px; word-wrap: break-word;">
                            Founded in 2020, we started with a simple mission: to make technology accessible to everyone.
                        </p>
                        <p style="font-size: 18px; color: #64748b; line-height: 1.8; margin-bottom: 20px; word-wrap: break-word;">
                            Today, we serve thousands of customers worldwide and continue to innovate every day.
                        </p>
                        <p style="font-size: 18px; color: #64748b; line-height: 1.8; word-wrap: break-word;">
                            Our commitment to excellence drives everything we do.
                        </p>
                    </div>
                `;
        }
    }

    createTeamWireframe(section, variant) {
        const team = [
            { name: 'John Smith', role: 'CEO & Founder', img: '👨‍💼' },
            { name: 'Sarah Johnson', role: 'CTO', img: '👩‍💻' },
            { name: 'Mike Davis', role: 'Head of Design', img: '👨‍🎨' },
            { name: 'Emily Brown', role: 'Marketing Director', img: '👩‍💼' }
        ];

        switch (variant) {
            case 'layout-grid-4':
                return `
                    <div class="team-grid ${variant}" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 24px; width: 100%;">
                        ${team.map(member => `
                            <div style="text-align: center; box-sizing: border-box;">
                                <div style="width: 100%; aspect-ratio: 1; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 64px; margin-bottom: 16px; box-sizing: border-box;">
                                    ${member.img}
                                </div>
                                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 4px; color: #1e293b; word-wrap: break-word;">${member.name}</h3>
                                <p style="font-size: 14px; color: #64748b; word-wrap: break-word;">${member.role}</p>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-cards':
                return `
                    <div class="team-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 32px; margin-top: 24px; width: 100%;">
                        ${team.map(member => `
                            <div style="background: #f8fafc; padding: 32px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; gap: 24px; align-items: center; box-sizing: border-box;">
                                <div style="width: 100px; height: 100px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 48px; flex-shrink: 0;">
                                    ${member.img}
                                </div>
                                <div style="flex: 1; min-width: 0;">
                                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 6px; color: #1e293b; word-wrap: break-word;">${member.name}</h3>
                                    <p style="font-size: 15px; color: #64748b; margin-bottom: 12px; word-wrap: break-word;">${member.role}</p>
                                    <div style="display: flex; gap: 8px;">
                                        <div style="width: 28px; height: 28px; background: #e2e8f0; border-radius: 50%;"></div>
                                        <div style="width: 28px; height: 28px; background: #e2e8f0; border-radius: 50%;"></div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-list':
            default:
                return `
                    <div class="team-list" style="display: flex; flex-direction: column; gap: 24px; margin-top: 24px; width: 100%;">
                        ${team.map(member => `
                            <div style="display: flex; gap: 24px; align-items: center; background: white; padding: 24px; border-radius: 12px; border: 2px solid #e2e8f0; box-sizing: border-box;">
                                <div style="width: 80px; height: 80px; background: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px; flex-shrink: 0;">
                                    ${member.img}
                                </div>
                                <div style="flex: 1; min-width: 0;">
                                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 4px; color: #1e293b; word-wrap: break-word;">${member.name}</h3>
                                    <p style="font-size: 15px; color: #64748b; word-wrap: break-word;">${member.role}</p>
                                </div>
                                <div style="display: flex; gap: 12px; flex-shrink: 0;">
                                    <div style="width: 32px; height: 32px; background: #e2e8f0; border-radius: 50%;"></div>
                                    <div style="width: 32px; height: 32px; background: #e2e8f0; border-radius: 50%;"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    createCultureWireframe(section, variant) {
        const values = [
            { icon: '🎯', title: 'Mission Driven', desc: 'We focus on what matters most' },
            { icon: '🤝', title: 'Collaborative', desc: 'We work together to achieve more' },
            { icon: '💪', title: 'Resilient', desc: 'We overcome challenges with determination' },
            { icon: '🌟', title: 'Innovative', desc: 'We constantly push boundaries' }
        ];

        switch (variant) {
            case 'layout-grid':
                return `
                    <div class="culture-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 32px; margin-top: 24px; width: 100%;">
                        ${values.map(v => `
                            <div style="background: #f8fafc; padding: 40px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-sizing: border-box;">
                                <div style="font-size: 56px; margin-bottom: 20px;">${v.icon}</div>
                                <h3 style="font-size: 22px; font-weight: 700; margin-bottom: 12px; color: #1e293b; word-wrap: break-word;">${v.title}</h3>
                                <p style="font-size: 15px; color: #64748b; line-height: 1.6; word-wrap: break-word;">${v.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-list':
                return `
                    <div class="culture-list" style="max-width: 700px; margin: 0 auto; width: 100%;">
                        ${values.map((v, i) => `
                            <div style="display: flex; gap: 24px; padding: 32px 0; ${i < values.length - 1 ? 'border-bottom: 1px solid #e2e8f0;' : ''} box-sizing: border-box;">
                                <div style="font-size: 48px; flex-shrink: 0;">${v.icon}</div>
                                <div style="flex: 1; min-width: 0;">
                                    <h3 style="font-size: 22px; font-weight: 700; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">${v.title}</h3>
                                    <p style="font-size: 16px; color: #64748b; line-height: 1.7; word-wrap: break-word;">${v.desc}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-cards':
            default:
                return `
                    <div class="culture-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 24px; margin-top: 24px; width: 100%;">
                        ${values.map(v => `
                            <div style="background: white; padding: 32px 24px; border-radius: 12px; border: 2px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); box-sizing: border-box;">
                                <div style="font-size: 48px; margin-bottom: 16px;">${v.icon}</div>
                                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e293b; word-wrap: break-word;">${v.title}</h3>
                                <p style="font-size: 14px; color: #64748b; line-height: 1.6; word-wrap: break-word;">${v.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    createLocationWireframe(section, variant) {
        switch (variant) {
            case 'layout-map-large':
                return `
                    <div class="location-map-large" style="margin-top: 24px; width: 100%;">
                        <div style="height: 400px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 24px; margin-bottom: 32px; box-sizing: border-box;">
                            🗺️ Interactive Map
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px;">
                            <div style="text-align: center; box-sizing: border-box;">
                                <div style="font-size: 32px; margin-bottom: 8px;">📍</div>
                                <h4 style="font-size: 16px; font-weight: 600; margin-bottom: 4px; color: #1e293b; word-wrap: break-word;">Address</h4>
                                <p style="font-size: 14px; color: #64748b; word-wrap: break-word;">123 Main Street<br/>City, State 12345</p>
                            </div>
                            <div style="text-align: center; box-sizing: border-box;">
                                <div style="font-size: 32px; margin-bottom: 8px;">📞</div>
                                <h4 style="font-size: 16px; font-weight: 600; margin-bottom: 4px; color: #1e293b; word-wrap: break-word;">Phone</h4>
                                <p style="font-size: 14px; color: #64748b; word-wrap: break-word;">+1 (555) 123-4567</p>
                            </div>
                            <div style="text-align: center; box-sizing: border-box;">
                                <div style="font-size: 32px; margin-bottom: 8px;">⏰</div>
                                <h4 style="font-size: 16px; font-weight: 600; margin-bottom: 4px; color: #1e293b; word-wrap: break-word;">Hours</h4>
                                <p style="font-size: 14px; color: #64748b; word-wrap: break-word;">Mon-Fri: 9AM-6PM<br/>Sat-Sun: Closed</p>
                            </div>
                        </div>
                    </div>
                `;

            case 'layout-split':
                return `
                    <div class="location-split ${variant}" style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 24px; width: 100%;">
                        <div style="height: 350px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 24px; box-sizing: border-box;">
                            🗺️ Map
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 24px; box-sizing: border-box;">
                            <div class="section-label" style="font-size: 14px; font-weight: 600; color: #64748b; margin-bottom: -16px; text-transform: uppercase; letter-spacing: 0.05em;">${section.title || 'Our Offices'}</div>
                            <div>
                                <div style="font-size: 32px; margin-bottom: 12px;">📍</div>
                                <h4 style="font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">Visit Us</h4>
                                <p style="font-size: 15px; color: #64748b; line-height: 1.6; word-wrap: break-word;">123 Main Street<br/>City, State 12345<br/>United States</p>
                            </div>
                            <div>
                                <div style="font-size: 32px; margin-bottom: 12px;">📞</div>
                                <h4 style="font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">Contact</h4>
                                <p style="font-size: 15px; color: #64748b; line-height: 1.6; word-wrap: break-word;">Phone: +1 (555) 123-4567<br/>Email: hello@company.com</p>
                            </div>
                            <div>
                                <div style="font-size: 32px; margin-bottom: 12px;">⏰</div>
                                <h4 style="font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">Business Hours</h4>
                                <p style="font-size: 15px; color: #64748b; line-height: 1.6; word-wrap: break-word;">Monday - Friday: 9:00 AM - 6:00 PM<br/>Saturday - Sunday: Closed</p>
                            </div>
                        </div>
                    </div>
                `;

            case 'layout-simple':
            default:
                return `
                    <div class="location-simple" style="max-width: 600px; margin: 40px auto; text-align: center; width: 100%; box-sizing: border-box;">
                        <div style="height: 250px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 24px; margin-bottom: 32px; box-sizing: border-box;">
                            🗺️ Map
                        </div>
                        <h3 style="font-size: 24px; font-weight: 700; margin-bottom: 16px; color: #1e293b; word-wrap: break-word;">Our Location</h3>
                        <p style="font-size: 16px; color: #64748b; margin-bottom: 8px; word-wrap: break-word;">123 Main Street, City, State 12345</p>
                        <p style="font-size: 16px; color: #64748b; margin-bottom: 8px; word-wrap: break-word;">Phone: +1 (555) 123-4567</p>
                        <p style="font-size: 16px; color: #64748b; word-wrap: break-word;">Email: hello@company.com</p>
                    </div>
                `;
        }
    }

    createMainInfoWireframe(section, variant) {
        if (!section.items || section.items.length === 0) {
            section.items = [
                { title: 'Analytics', desc: 'Detailed data analysis insights.', icon: '📊' },
                { title: 'Security', desc: 'Advanced data protection protocols.', icon: '🔒' },
                { title: 'Performance', desc: 'Optimized speed and efficiency.', icon: '⚡' },
                { title: 'Optimization', desc: 'Resource usage optimization.', icon: '🔍' }
            ];
            this.syncSectionData(section);
        }
        const items = section.items;
        const v = (variant || 'layout-default').toLowerCase();

        // Style for cards (consistent with premium design)
        const cardStyle = `padding: 32px; background: white; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: all 0.3s ease; box-sizing: border-box; border: none;`;

        let contentHtml = '';
        let containerStyle = `display: grid; gap: 32px; width: 100%; max-width: 1280px; margin: 0 auto; padding: 0 24px; box-sizing: border-box;`;

        if (v === 'layout-list') {
            containerStyle = `display: flex; flex-direction: column; gap: 24px; width: 100%; max-width: 900px; margin: 0 auto; padding: 0 24px; box-sizing: border-box;`;
            contentHtml = items.map((item, i) => `
                <div class="feature-card" style="display: flex; gap: 24px; padding: 32px; background: white; border-radius: 12px; text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.05); align-items: center; border: none;">
                    <div style="font-size: 48px; flex-shrink: 0;">${item.icon}</div>
                    <div>
                        <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 20px; font-weight: 600; color: #1e293b; margin-bottom: 8px;">${item.title}</h4>
                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 14px; color: #64748b; line-height: 1.6;">${item.desc}</p>
                    </div>
                </div>
            `).join('');
        } else if (v === 'layout-centered') {
            containerStyle = `display: flex; flex-direction: column; gap: 48px; width: 100%; max-width: 800px; margin: 0 auto; padding: 0 24px; box-sizing: border-box;`;
            contentHtml = items.map((item, i) => `
                <div class="feature-card" style="text-align: center; padding: 40px; border-bottom: 1px solid #f1f5f9;">
                    <div style="font-size: 64px; margin-bottom: 24px;">${item.icon}</div>
                    <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">${item.title}</h4>
                    <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 16px; color: #64748b; line-height: 1.8; max-width: 600px; margin: 0 auto;">${item.desc}</p>
                </div>
            `).join('');
        } else {
            // Grid variants (2, 3, 4 columns)
            let cols = 3;
            if (v.includes('-2')) cols = 2;
            else if (v.includes('-4')) cols = 4;
            else if (v === 'layout-split') cols = 2;

            containerStyle += ` grid-template-columns: repeat(${cols}, 1fr);`;

            contentHtml = items.map((item, i) => `
                <div class="feature-card" style="${cardStyle}">
                    <div style="font-size: 48px; margin-bottom: 16px;">${item.icon}</div>
                    <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 20px; font-weight: 600; color: #1e293b; margin-bottom: 8px;">${item.title}</h4>
                    <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 14px; color: #64748b; line-height: 1.6;">${item.desc}</p>
                </div>
            `).join('');
        }

        return `
            <div class="main-info-section" style="padding: 80px 0; width: 100%; box-sizing: border-box;">
                <h2 class="editable-text" data-field="title" style="font-size: 36px; font-weight: 700; margin-bottom: 48px; color: #1e293b; text-align: center; width: 100%; max-width: 1280px; margin-left: auto; margin-right: auto;">${section.title || 'Main Information'}</h2>
                <div class="feature-card-grid" style="${containerStyle}">
                    ${contentHtml}
                </div>
                <style>
                    .feature-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important; }
                    @media (max-width: 768px) {
                        .feature-card-grid { grid-template-columns: 1fr !important; }
                        .feature-card { padding: 24px !important; }
                    }
                </style>
            </div>
        `;
    }

    createSupportingInfoWireframe(section, variant) {
        if (!section.items || section.items.length === 0) {
            section.items = [
                { title: 'Analytics', desc: 'Detailed data analysis insights.', icon: '📊' },
                { title: 'Security', desc: 'Advanced data protection protocols.', icon: '🔒' },
                { title: 'Performance', desc: 'Optimized speed and efficiency.', icon: '⚡' },
                { title: 'Optimization', desc: 'Resource usage optimization.', icon: '🔍' }
            ];
            this.syncSectionData(section);
        }
        const items = section.items;

        const listHtml = `
            ${items.map((item, i) => `
                <div style="display: flex; gap: 24px; padding: 24px; background: ${i % 2 === 0 ? '#f8fafc' : 'white'}; border-radius: 12px; margin-bottom: 16px; border: 1px solid #e2e8f0; box-sizing: border-box; align-items: flex-start;">
                    <div style="font-size: 36px; flex-shrink: 0;">${item.icon}</div>
                    <div style="flex: 1; min-width: 0;">
                        <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 20px; font-weight: 600; margin-bottom: 8px; color: #1e293b;">${item.title}</h4>
                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 15px; color: #64748b; line-height: 1.7;">${item.desc}</p>
                    </div>
                </div>
            `).join('')}
        `;

        switch (variant) {
            case 'layout-grid-2':
            case 'layout-grid-3':
            case 'layout-grid-4':
            case 'layout-grid':
                const spCols = variant.includes('-2') ? 2 : variant.includes('-4') ? 4 : 3;
                return `
                    <div class="supporting-info-grid" style="width: 100%; box-sizing: border-box; padding: 40px 0;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center; color: #1e293b;">${section.title || 'Supporting Content'}</h3>
                        <div style="display: grid; grid-template-columns: repeat(${spCols}, 1fr); gap: 24px;">
                            ${items.map((item, i) => `
                                <div style="padding: 24px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
                                    <div style="font-size: 36px; margin-bottom: 12px;">${item.icon}</div>
                                    <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 8px;">${item.title}</h4>
                                    <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 13px; color: #64748b; line-height: 1.6;">${item.desc}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-cards':
                return `
                    <div class="supporting-info-cards" style="width: 100%; box-sizing: border-box;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center; color: #1e293b;">${section.title || 'Supporting Content'}</h3>
                        <div style="display: flex; gap: 20px; overflow-x: auto; padding: 20px 0;">
                            ${items.map((item, i) => `
                                <div style="flex: 0 0 300px; padding: 32px; background: #f8fafc; border-radius: 16px; border: 1px solid #e2e8f0;">
                                    <div style="font-size: 40px; margin-bottom: 20px;">${item.icon}</div>
                                    <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">${item.title}</h4>
                                    <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 15px; color: #64748b;">${item.desc}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-list':
            case 'layout-default':
            default:
                return `
                    <div class="supporting-info-list" style="max-width: 900px; margin: 0 auto; width: 100%; box-sizing: border-box;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center; color: #1e293b;">${section.title || 'Supporting Content'}</h3>
                        ${listHtml}
                    </div>
                `;

            case 'layout-sidebar':
                return `
                    <div class="supporting-info-sidebar" style="display: grid; grid-template-columns: 2fr 1fr; gap: 40px; margin-top: 24px; width: 100%;">
                        <div style="box-sizing: border-box;">
                            <h3 class="editable-text" data-field="title" style="font-size: 28px; font-weight: 700; margin-bottom: 20px; color: #1e293b;">${section.title || 'Supporting Information'}</h3>
                            <p class="editable-text" data-field="description" style="font-size: 16px; color: #64748b; line-height: 1.8; margin-bottom: 24px;">
                                ${section.description || 'Additional details and supporting information to help you understand our offerings better.'}
                            </p>
                            <div style="display: flex; flex-direction: column; gap: 12px;">
                                ${items.map((item, i) => `
                                    <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: white; border-radius: 8px; border: 1px solid #e2e8f0;">
                                        <span style="color: #10b981; font-size: 18px;">✓</span>
                                        <span class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 14px; color: #475569;">${item.title}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div style="background: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; box-sizing: border-box;">
                            <h4 style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1e293b;">Quick Facts</h4>
                            ${items.slice(0, 3).map((item, i) => `
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding: 12px; background: white; border-radius: 8px;">
                                    <span style="font-size: 18px;">${item.icon}</span>
                                    <span style="font-size: 14px; color: #475569;">${item.title}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-tabs':
                return `
                    <div class="supporting-info-tabs" style="max-width: 1000px; margin: 0 auto; width: 100%; box-sizing: border-box;">
                        <div style="display: flex; gap: 8px; border-bottom: 2px solid #e2e8f0; margin-bottom: 32px; flex-wrap: wrap;">
                            ${items.map((item, i) => `
                                <button style="padding: 12px 24px; background: ${i === 0 ? '#6366f1' : 'transparent'}; color: ${i === 0 ? 'white' : '#64748b'}; border: none; border-bottom: 3px solid ${i === 0 ? '#6366f1' : 'transparent'}; font-size: 15px; font-weight: 600; cursor: pointer; border-radius: 8px 8px 0 0;">${item.title}</button>
                            `).join('')}
                        </div>
                        <div style="padding: 24px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                            <h4 class="editable-text" data-field="item-title" data-index="0" style="font-size: 24px; font-weight: 700; margin-bottom: 16px; color: #1e293b;">${items[0].title}</h4>
                            <p class="editable-text" data-field="item-desc" data-index="0" style="font-size: 16px; color: #64748b; line-height: 1.8;">${items[0].desc}</p>
                        </div>
                    </div>
                `;

            case 'layout-bento':


                // Emphasize the first item (e.g. Analytics)
                const mainItem = items[0];
                const otherItems = items.slice(1);

                return `
                    <div class="supporting-info-bento" style="max-width: 900px; margin: 0 auto; width: 100%;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center; color: #1e293b;">${section.title || 'Supporting Content'}</h3>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                            <!-- Main Feature (Large) -->
                            <div style="grid-column: span 2; background: linear-gradient(135deg, #6366f1, #818cf8); padding: 40px; border-radius: 24px; color: white;">
                                <div style="font-size: 48px; margin-bottom: 24px;">${mainItem.icon}</div>
                                <h4 class="editable-text" data-field="item-title" data-index="0" style="font-size: 28px; font-weight: 700; margin-bottom: 16px;">${mainItem.title}</h4>
                                <p class="editable-text" data-field="item-desc" data-index="0" style="font-size: 18px; line-height: 1.6; opacity: 0.95;">${mainItem.desc}</p>
                            </div>

                            <!-- Secondary Features -->
                            ${otherItems.map((item, i) => `
                                <div style="background: white; padding: 32px; border-radius: 24px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: center;">
                                    <div style="font-size: 40px; margin-bottom: 16px;">${item.icon}</div>
                                    <h4 class="editable-text" data-field="item-title" data-index="${i + 1}" style="font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">${item.title}</h4>
                                    <p class="editable-text" data-field="item-desc" data-index="${i + 1}" style="font-size: 15px; color: #64748b; line-height: 1.6;">${item.desc.substring(0, 100)}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-accordion':
                return `
                    <div class="supporting-info-accordion" style="max-width: 800px; margin: 0 auto; width: 100%;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 32px; text-align: center; color: #1e293b;">${section.title || 'Supporting Content'}</h3>
                        ${items.map((item, i) => `
                            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; margin-bottom: 16px; overflow: hidden; box-sizing: border-box;">
                                <div style="padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; background: ${i === 0 ? '#f8fafc' : 'white'};">
                                    <h4 class="editable-text" data-field="item-title" data-index="${i}" style="font-size: 18px; font-weight: 600; color: #1e293b; margin: 0;">${item.title}</h4>
                                    <span style="font-size: 20px; color: #64748b;">${i === 0 ? '−' : '+'}</span>
                                </div>
                                ${i === 0 ? `
                                    <div style="padding: 0 24px 20px 24px; border-top: 1px solid #e2e8f0;">
                                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size: 15px; color: #64748b; line-height: 1.7; margin-top: 16px;">
                                            ${item.desc}
                                        </p>
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    createKeyFeaturesWireframe(section, variant) {
        const features = [
            { icon: '⚡', title: 'Fast Performance', desc: 'Lightning-fast load times and smooth interactions' },
            { icon: '🔒', title: 'Secure Platform', desc: 'Enterprise-grade security and data protection' },
            { icon: '📱', title: 'Mobile Ready', desc: 'Fully responsive across all devices' },
            { icon: '🎯', title: 'Easy to Use', desc: 'Intuitive interface designed for everyone' }
        ];

        switch (variant) {
            case 'layout-grid-3':
                return `
                    <div class="key-features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 32px; margin-top: 24px; width: 100%;">
                        ${features.slice(0, 3).map(f => `
                            <div style="background: white; padding: 40px 32px; border-radius: 12px; border: 2px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); box-sizing: border-box;">
                                <div style="font-size: 56px; margin-bottom: 20px;">${f.icon}</div>
                                <h3 style="font-size: 22px; font-weight: 700; margin-bottom: 12px; color: #1e293b; word-wrap: break-word;">${f.title}</h3>
                                <p style="font-size: 15px; color: #64748b; line-height: 1.7; word-wrap: break-word;">${f.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-list':
                return `
                    <div class="key-features-list" style="max-width: 800px; margin: 0 auto; width: 100%;">
                        ${features.map((f, i) => `
                            <div style="display: flex; gap: 24px; align-items: start; padding: 32px 0; ${i < features.length - 1 ? 'border-bottom: 1px solid #e2e8f0;' : ''} box-sizing: border-box;">
                                <div style="font-size: 48px; flex-shrink: 0;">${f.icon}</div>
                                <div style="flex: 1; min-width: 0;">
                                    <h3 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #1e293b; word-wrap: break-word;">${f.title}</h3>
                                    <p style="font-size: 16px; color: #64748b; line-height: 1.8; word-wrap: break-word;">${f.desc}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-cards':
                return `
                    <div class="key-features-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; margin-top: 24px; width: 100%;">
                        ${features.map(f => `
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 36px 28px; border-radius: 16px; text-align: center; color: white; box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3); box-sizing: border-box;">
                                <div style="font-size: 52px; margin-bottom: 16px;">${f.icon}</div>
                                <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 12px; word-wrap: break-word;">${f.title}</h3>
                                <p style="font-size: 14px; opacity: 0.95; line-height: 1.6; word-wrap: break-word;">${f.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-horizontal':
                return `
                    <div class="key-features-horizontal" style="display: flex; gap: 24px; overflow-x: auto; padding: 24px 0; scroll-snap-type: x mandatory; width: 100%;">
                        ${features.map(f => `
                            <div style="min-width: 300px; background: white; padding: 32px; border-radius: 12px; border: 2px solid #e2e8f0; text-align: center; scroll-snap-align: start; box-sizing: border-box;">
                                <div style="font-size: 48px; margin-bottom: 16px;">${f.icon}</div>
                                <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 12px; color: #1e293b; word-wrap: break-word;">${f.title}</h3>
                                <p style="font-size: 14px; color: #64748b; line-height: 1.6; word-wrap: break-word;">${f.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;

            case 'layout-minimal':
                return `
                    <div class="key-features-minimal" style="max-width: 900px; margin: 0 auto; width: 100%;">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px;">
                            ${features.map(f => `
                                <div style="display: flex; gap: 20px; align-items: start; box-sizing: border-box;">
                                    <div style="font-size: 40px; flex-shrink: 0;">${f.icon}</div>
                                    <div style="flex: 1; min-width: 0;">
                                        <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 8px; color: #1e293b; word-wrap: break-word;">${f.title}</h3>
                                        <p style="font-size: 15px; color: #64748b; line-height: 1.7; word-wrap: break-word;">${f.desc}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-featured':
                return `
                    <div class="key-features-featured" style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 24px; width: 100%;">
                        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 48px 40px; border-radius: 16px; color: white; display: flex; flex-direction: column; justify-content: center; box-sizing: border-box;">
                            <div style="font-size: 64px; margin-bottom: 20px;">${features[0].icon}</div>
                            <h3 style="font-size: 32px; font-weight: 700; margin-bottom: 16px; word-wrap: break-word;">${features[0].title}</h3>
                            <p style="font-size: 18px; opacity: 0.95; line-height: 1.7; word-wrap: break-word;">${features[0].desc}</p>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 20px;">
                            ${features.slice(1).map(f => `
                                <div style="background: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; gap: 20px; align-items: center; box-sizing: border-box;">
                                    <div style="font-size: 40px; flex-shrink: 0;">${f.icon}</div>
                                    <div style="flex: 1; min-width: 0;">
                                        <h4 style="font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #1e293b; word-wrap: break-word;">${f.title}</h4>
                                        <p style="font-size: 14px; color: #64748b; line-height: 1.6; word-wrap: break-word;">${f.desc}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

            case 'layout-grid-4':
            default:
                return `
                    <div class="key-features-grid-4" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; margin-top: 24px; width: 100%;">
                        ${features.map(f => `
                            <div style="background: #f8fafc; padding: 32px 24px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-sizing: border-box;">
                                <div style="font-size: 48px; margin-bottom: 16px;">${f.icon}</div>
                                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e293b; word-wrap: break-word;">${f.title}</h3>
                                <p style="font-size: 14px; color: #64748b; line-height: 1.6; word-wrap: break-word;">${f.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                `;
        }
    }

    // Bind events to section elements
    bindSectionEvents(sectionEl, section, index, pageId) {
        // Section button (open layout options)
        const sectionBtn = sectionEl.querySelector('.section-btn');
        if (sectionBtn) {
            sectionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openLayoutOptions(section, index, pageId, sectionEl);
            });
        }

        // Delete button
        const deleteBtn = sectionEl.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSection(pageId, index);
            });
        }

        // Text editing
        sectionEl.querySelectorAll('.editable-text').forEach(textEl => {
            textEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.makeTextEditable(textEl, pageId, index);
            });
        });

        // Click on section to select it (optional, but good UX)
        sectionEl.addEventListener('click', (e) => {
            // Only if not clicking a control
            if (!e.target.closest('.toolbar-btn') && !e.target.closest('.inline-editor')) {
                this.selectSection(section, index, pageId, sectionEl);
            }
        });
    }

    selectSection(section, index, pageId, element) {
        if (this.activeSection && this.activeSection.element) {
            this.activeSection.element.classList.remove('selected');
            const prevColumn = document.querySelector(`.wireframe-page-column[data-page-id="${this.activeSection.pageId}"]`);
            if (prevColumn) prevColumn.classList.remove('page-highlight');
        }
        this.activeSection = { section, index, pageId, element };
        element.classList.add('selected');
        const column = document.querySelector(`.wireframe-page-column[data-page-id="${pageId}"]`);
        if (column) column.classList.add('page-highlight');
    }

    async openLayoutOptions(section, index, pageId, element) {
        // Activate section
        if (this.activeSection && this.activeSection.element) {
            this.activeSection.element.classList.remove('selected');
        }
        this.activeSection = { section, index, pageId, element };
        element.classList.add('selected');

        // Open sidebar and show loading state
        const sidebar = document.getElementById('sectionSettingsSidebar');
        const replaceView = document.getElementById('sidebarReplaceView');
        const nameSpan = document.getElementById('suggestionSectionName');

        if (nameSpan) nameSpan.textContent = `Layout Options for ${section.type.charAt(0).toUpperCase() + section.type.slice(1)}`;
        if (sidebar) sidebar.classList.add('active');
        if (replaceView) replaceView.classList.add('active');

        const list = document.getElementById('suggestionList');
        if (list) {
            list.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;">Loading layout options...</div>';

            // Generate layout options using AI
            const layouts = await this.generateLayoutOptions(section.type);

            list.innerHTML = layouts.map((layout, i) => `
                <div class="suggestion-card layout-option-card" data-idx="${i}">
                    <div class="layout-preview">
                        <div class="layout-thumbnail">${layout.preview}</div>
                    </div>
                    <div class="layout-info">
                        <div class="layout-name">${layout.name}</div>
                        <div class="layout-description">${layout.description}</div>
                    </div>
                </div>
            `).join('');

            // Bind click events
            list.querySelectorAll('.suggestion-card').forEach(card => {
                card.addEventListener('click', () => {
                    const idx = parseInt(card.dataset.idx);
                    this.applyLayoutOption(layouts[idx]);
                });
            });
        }
    }

    async generateLayoutOptions(sectionType) {
        // Use AI API to generate layout variations
        const apiKey = await this.getPrivateKey();

        if (!apiKey) {
            console.warn('DEBUG: No API key found. Using Hardcoded Fallback layouts.');
            console.error('No API key found');
            return this.getFallbackLayouts(sectionType);
        }

        console.log('DEBUG: API Key found. Attempting AI Layout Generation...');

        try {
            const prompt = this.getLayoutPrompt(sectionType);
            const baseUrl = (this.aiConfig && this.aiConfig.wireframe && this.aiConfig.wireframe.base_url)
                ? this.aiConfig.wireframe.base_url
                : 'https://openrouter.ai/api/v1/chat/completions';
            const model = (this.aiConfig && this.aiConfig.wireframe && this.aiConfig.wireframe.model)
                ? this.aiConfig.wireframe.model
                : 'meta-llama/llama-3.2-3b-instruct:free';

            const response = await fetch(baseUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': window.location.origin,
                },
                body: JSON.stringify({
                    model,
                    messages: [{
                        role: 'user',
                        content: prompt
                    }]
                })
            });

            if (!response.ok) {
                throw new Error('API request failed');
            }

            const data = await response.json();
            const layoutsText = data.choices[0].message.content;

            console.log('DEBUG: AI Response received successfully:', layoutsText.substring(0, 100) + '...');
            console.log('DEBUG: Parsing AI response...');

            // Parse the AI response into layout objects
            return this.parseLayoutResponse(layoutsText, sectionType);

        } catch (error) {
            console.error('Error generating layouts:', error);
            console.warn('DEBUG: AI Generation failed. Switching to Hardcoded Fallback layouts.');
            return this.getFallbackLayouts(sectionType);
        }
    }

    async getPrivateKey() {
        try {
            // Disabled API call - not needed for export functionality
            const response = await fetch('/api/config/');
            const data = await response.json();
            this.aiConfig = data.ai || {};
            return data.private_key;
            return null; // Return null to skip API key requirement
        } catch (error) {
            console.error('Error fetching API key:', error);
            return null;
        }
    }

    getLayoutPrompt(sectionType) {
        const prompts = {
            hero: `Generate 12 different layout variations for a hero section. For each layout, provide:
1. A unique name (e.g., "Split Screen Bold", "Centered Minimal", "Asymmetric Dynamic")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            features: `Generate 12 different layout variations for a features section. For each layout, provide:
1. A unique name (e.g., "Grid 3-Column", "Staggered Cards", "Horizontal Scroll")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of feature items)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            navbar: `Generate 12 different layout variations for a navigation bar. For each layout, provide:
1. A unique name (e.g., "Classic Horizontal", "Sidebar Vertical", "Mega Menu")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of nav elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            testimonial: `Generate 12 different layout variations for a testimonial section. For each layout, provide:
1. A unique name (e.g., "Carousel Slider", "Grid Masonry", "Featured Quote")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of testimonials)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            footer: `Generate 12 different layout variations for a footer section. For each layout, provide:
1. A unique name (e.g., "Multi-Column", "Centered Minimal", "Newsletter Focus")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of footer elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            about: `Generate 12 different layout variations for an about section. For each layout, provide:
1. A unique name (e.g., "Story Timeline", "Team Grid", "Mission Statement")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of about content)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            contact: `Generate 12 different layout variations for a contact section. For each layout, provide:
1. A unique name (e.g., "Form with Map", "Split Contact Info", "Centered Form")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of contact elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            pricing: `Generate 12 different layout variations for a pricing section. For each layout, provide:
1. A unique name (e.g., "3-Tier Cards", "Comparison Table", "Toggle Monthly/Yearly")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of pricing plans)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            gallery: `Generate 12 different layout variations for a gallery/portfolio section. For each layout, provide:
1. A unique name (e.g., "Masonry Grid", "Lightbox Carousel", "Filterable Grid")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of images)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            blog: `Generate 12 different layout variations for a blog section. For each layout, provide:
1. A unique name (e.g., "Card Grid", "List with Sidebar", "Featured Post")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of blog posts)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            stats: `Generate 12 different layout variations for a statistics/metrics section. For each layout, provide:
1. A unique name (e.g., "Counter Grid", "Circular Progress", "Animated Numbers")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of stats)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            cta: `Generate 12 different layout variations for a call-to-action section. For each layout, provide:
1. A unique name (e.g., "Centered Bold", "Split with Image", "Banner Style")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of CTA elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            services: `Generate 12 different layout variations for a services section. For each layout, provide:
1. A unique name (e.g., "Service Cards Grid", "Icon List", "Tabbed Services")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of service offerings)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            story: `Generate 12 different layout variations for a company story/history section. For each layout, provide:
1. A unique name (e.g., "Timeline Vertical", "Milestone Cards", "Narrative Flow")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of story elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            team: `Generate 12 different layout variations for a team members section. For each layout, provide:
1. A unique name (e.g., "Team Grid", "Profile Cards", "Carousel Slider")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of team member profiles)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            culture: `Generate 12 different layout variations for a company culture/values section. For each layout, provide:
1. A unique name (e.g., "Values Grid", "Icon Blocks", "Image Overlay")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of culture/values content)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            location: `Generate 12 different layout variations for a location/map section. For each layout, provide:
1. A unique name (e.g., "Map Dominant", "Split Map Info", "Multi-Location Grid")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of map and location details)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            information: `Generate 12 different layout variations for an information section. For each layout, provide:
1. A unique name (e.g., "Info Cards", "List Layout", "Grid Blocks")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of information content)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            'contact-details': `Generate 12 different layout variations for a contact details section. For each layout, provide:
1. A unique name (e.g., "Contact Cards", "List with Icons", "Split Layout")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of contact information)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            'main-info': `Generate 12 different layout variations for a main information section. For each layout, provide:
1. A unique name (e.g., "Hero Style", "Featured Content", "Centered Focus")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of primary content)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`,

            'supporting-info': `Generate 12 different layout variations for a supporting information section. For each layout, provide:
1. A unique name (e.g., "Sidebar Layout", "Accordion Style", "Grid Blocks")
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of supporting content)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`
        };

        return prompts[sectionType] || `Generate 12 different layout variations for a ${sectionType} section. For each layout, provide:
1. A unique name
2. A brief description (1 sentence)
3. Layout structure (describe the arrangement of elements)

Format each as:
NAME: [name]
DESC: [description]
STRUCTURE: [structure description]
---`;
    }

    parseLayoutResponse(text, sectionType) {
        const layouts = [];
        const sections = text.split('---').filter(s => s.trim());

        sections.forEach((section, index) => {
            const nameMatch = section.match(/NAME:\s*(.+)/i);
            const descMatch = section.match(/DESC:\s*(.+)/i);
            const structureMatch = section.match(/STRUCTURE:\s*(.+)/i);

            if (nameMatch && descMatch) {
                const layoutName = nameMatch[1].trim();
                // Convert layout name to a valid CSS class name
                const layoutClass = this.generateLayoutClass(layoutName, sectionType, index);

                layouts.push({
                    name: layoutName,
                    description: descMatch[1].trim(),
                    structure: structureMatch ? structureMatch[1].trim() : '',
                    preview: this.generateLayoutPreview(sectionType, index),
                    layoutClass: layoutClass
                });
            }
        });

        return layouts.length > 0 ? layouts : this.getFallbackLayouts(sectionType);
    }

    generateLayoutClass(layoutName, sectionType, index) {
        // Map common layout names to existing layout classes
        const nameLower = layoutName.toLowerCase();

        // Common patterns that map to existing layouts
        const mappings = {
            // Grid patterns
            'grid': 'layout-grid-3',
            '3-column': 'layout-grid-3',
            '3 column': 'layout-grid-3',
            'three column': 'layout-grid-3',
            '2-column': 'layout-grid-2',
            '2 column': 'layout-grid-2',
            'two column': 'layout-grid-2',
            '4-column': 'layout-grid-4',
            '4 column': 'layout-grid-4',
            'four column': 'layout-grid-4',

            // Split patterns
            'split': 'layout-split',
            'split right': 'layout-split-right',
            'split left': 'layout-split-left',
            'divided': 'layout-split',

            // Centered patterns
            'centered': 'layout-centered',
            'center': 'layout-centered',
            'middle': 'layout-centered',

            // Carousel/Slider patterns
            'carousel': 'layout-carousel',
            'slider': 'layout-carousel',
            'scroll': 'layout-horizontal',
            'horizontal': 'layout-horizontal',

            // List patterns
            'list': 'layout-list',
            'vertical': 'layout-list',

            // Masonry patterns
            'masonry': 'layout-masonry',
            'pinterest': 'layout-masonry',

            // Card patterns
            'card': 'layout-card',
            'cards': 'layout-cards',

            // Featured patterns
            'featured': 'layout-featured',
            'highlight': 'layout-featured',

            // Minimal patterns
            'minimal': 'layout-minimal',
            'simple': 'layout-minimal',
            'clean': 'layout-minimal',

            // Banner patterns
            'banner': 'layout-banner',
            'full width': 'layout-full-width',
            'fullwidth': 'layout-full-width',

            // Stacked patterns
            'stacked': 'layout-stacked',
            'vertical stack': 'layout-stacked',

            // Timeline patterns
            'timeline': 'layout-timeline',
            'chronological': 'layout-timeline',

            // Tabs patterns
            'tabs': 'layout-tabs',
            'tabbed': 'layout-tabs',

            // Bento patterns
            'bento': 'layout-bento',
            'mixed': 'layout-bento',

            // Staggered patterns
            'staggered': 'layout-staggered',
            'offset': 'layout-staggered',

            // Sidebar patterns
            'sidebar': 'layout-sidebar',
            'side': 'layout-sidebar',

            // Mega menu patterns
            'mega': 'layout-mega',
            'mega menu': 'layout-mega',

            // Hamburger patterns
            'hamburger': 'layout-hamburger',
            'mobile': 'layout-hamburger',

            // Sticky patterns
            'sticky': 'layout-sticky',
            'fixed': 'layout-sticky',

            // Transparent patterns
            'transparent': 'layout-transparent',
            'overlay': 'layout-transparent',

            // Diagonal patterns
            'diagonal': 'layout-diagonal',
            'angled': 'layout-diagonal',

            // Asymmetric patterns
            'asymmetric': 'layout-asymmetric',
            'uneven': 'layout-asymmetric',

            // Full background patterns
            'full background': 'layout-full-bg',
            'background': 'layout-full-bg',

            // Video patterns
            'video': 'layout-video-bg',
            'video background': 'layout-video-bg',

            // Bold text patterns
            'bold': 'layout-bold-text',
            'large text': 'layout-bold-text',
            'typography': 'layout-bold-text',

            // Explicit Full Matches (for robustness)
            'grid 4-column': 'layout-grid-4',
            'grid 4 column': 'layout-grid-4',
            'split layout': 'layout-split'
        };

        // Check for matches
        for (const [pattern, layoutClass] of Object.entries(mappings)) {
            if (nameLower.includes(pattern)) {
                return layoutClass;
            }
        }

        // If no match found, create a generic layout class
        return `layout-variant-${index}`;
    }

    generateLayoutPreview(sectionType, index) {
        // Generate simple SVG previews for different layout types
        const previews = {
            hero: [
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="5" y="10" width="40" height="40" fill="#e2e8f0"/><rect x="55" y="15" width="35" height="8" fill="#cbd5e1"/><rect x="55" y="28" width="30" height="4" fill="#cbd5e1"/><rect x="55" y="35" width="20" height="6" fill="#6366f1"/></svg>',
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="30" y="10" width="40" height="8" fill="#cbd5e1"/><rect x="35" y="22" width="30" height="4" fill="#cbd5e1"/><rect x="40" y="30" width="20" height="6" fill="#6366f1"/><rect x="25" y="40" width="50" height="15" fill="#e2e8f0"/></svg>',
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="55" y="10" width="40" height="40" fill="#e2e8f0"/><rect x="5" y="15" width="35" height="8" fill="#cbd5e1"/><rect x="5" y="28" width="30" height="4" fill="#cbd5e1"/><rect x="5" y="35" width="20" height="6" fill="#6366f1"/></svg>',
            ],
            features: [
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="5" y="10" width="25" height="40" fill="#e2e8f0"/><rect x="37" y="10" width="25" height="40" fill="#e2e8f0"/><rect x="69" y="10" width="25" height="40" fill="#e2e8f0"/></svg>',
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="5" y="5" width="40" height="20" fill="#e2e8f0"/><rect x="55" y="5" width="40" height="20" fill="#e2e8f0"/><rect x="5" y="30" width="40" height="20" fill="#e2e8f0"/><rect x="55" y="30" width="40" height="20" fill="#e2e8f0"/></svg>',
                '<svg viewBox="0 0 100 60" style="width:100%;height:80px;"><rect x="10" y="10" width="80" height="12" fill="#e2e8f0"/><rect x="10" y="25" width="80" height="12" fill="#e2e8f0"/><rect x="10" y="40" width="80" height="12" fill="#e2e8f0"/></svg>',
            ],
            navbar: [
                '<svg viewBox="0 0 100 20" style="width:100%;height:40px;"><rect x="5" y="5" width="15" height="10" fill="#6366f1"/><rect x="60" y="7" width="8" height="6" fill="#cbd5e1"/><rect x="70" y="7" width="8" height="6" fill="#cbd5e1"/><rect x="80" y="7" width="8" height="6" fill="#cbd5e1"/></svg>',
                '<svg viewBox="0 0 100 20" style="width:100%;height:40px;"><rect x="40" y="5" width="20" height="10" fill="#6366f1"/><rect x="10" y="7" width="8" height="6" fill="#cbd5e1"/><rect x="20" y="7" width="8" height="6" fill="#cbd5e1"/><rect x="70" y="7" width="8" height="6" fill="#cbd5e1"/><rect x="80" y="7" width="8" height="6" fill="#cbd5e1"/></svg>',
                '<svg viewBox="0 0 100 20" style="width:100%;height:40px;"><rect x="5" y="5" width="15" height="10" fill="#6366f1"/><rect x="25" y="7" width="65" height="6" fill="#e2e8f0"/></svg>',
            ]
        };

        const typePreview = previews[sectionType] || previews.hero;
        return typePreview[index % typePreview.length];
    }

    getFallbackLayouts(sectionType) {
        // Fallback layouts if AI fails
        const fallbacks = {
            services: [
                { name: 'Card Grid', description: 'Two-column card layout', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: '3-Column Grid', description: 'Three equal columns', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-3' },
                { name: '4-Column Grid', description: 'Four equal columns', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-4' },
                { name: 'List View', description: 'Vertical list with icons', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Horizontal Scroll', description: 'Horizontally scrolling cards', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-horizontal' },
                { name: 'Featured Service', description: 'One large featured service', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-featured' },
                { name: 'Minimal Layout', description: 'Clean minimal design', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-minimal' },
                { name: 'Carousel Slider', description: 'Sliding carousel of services', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-carousel' },
                { name: 'Split Layout', description: 'Content and image side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Masonry Grid', description: 'Pinterest-style masonry layout', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-masonry' },
                { name: 'Tabbed Interface', description: 'Tabbed service display', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-tabs' },
            ],
            story: [
                { name: 'Timeline', description: 'Chronological timeline layout', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-timeline' },
                { name: 'Split Layout', description: 'Image and content side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Centered', description: 'Centered story content', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
            ],
            team: [
                { name: 'Grid 4-Column', description: 'Four team members in a row', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-4' },
                { name: 'Card Layout', description: 'Team cards with details', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: 'List View', description: 'Vertical list of team members', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
            ],
            culture: [
                { name: 'Grid Layout', description: 'Values in grid format', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid' },
                { name: 'List View', description: 'Vertical list of values', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Card Layout', description: 'Value cards display', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
            ],
            location: [
                { name: 'Map Large', description: 'Large map with contact info', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-map-large' },
                { name: 'Split Layout', description: 'Map and details side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Simple', description: 'Simple centered location info', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-simple' },
            ],
            information: [
                { name: 'Card Layout', description: 'Information in cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: 'List View', description: 'Vertical list of information', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Grid Layout', description: 'Information grid display', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid' },
            ],
            'contact-details': [
                { name: 'Card Layout', description: 'Contact info in cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: 'List View', description: 'Vertical list of contact methods', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Split Layout', description: 'Contact info and hours split', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Grid 3-Column', description: 'Three contact cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-3' },
                { name: 'Minimal', description: 'Simple centered layout', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-minimal' },
                { name: 'Featured', description: 'Featured contact options', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-featured' },
            ],
            'main-info': [
                { name: 'Featured Layout', description: 'Large featured display', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-featured' },
                { name: 'Centered', description: 'Centered main information', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
                { name: 'Hero Style', description: 'Bold hero-style layout', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-hero' },
            ],
            'supporting-info': [
                { name: 'Grid Layout', description: 'Supporting info in grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid' },
                { name: 'Sidebar Layout', description: 'Content with sidebar', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-sidebar' },
                { name: 'Accordion', description: 'Expandable accordion items', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-accordion' },
            ],
            'contact-form': [],
            'key-features': [
                { name: 'Grid 4-Column', description: 'Four features in a row', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-4' },
                { name: 'Grid 3-Column', description: 'Three features in a row', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-3' },
                { name: 'List View', description: 'Vertical list of features', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Gradient Cards', description: 'Colorful gradient feature cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: 'Horizontal Scroll', description: 'Scrollable feature cards', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-horizontal' },
                { name: 'Minimal Layout', description: 'Clean minimal design', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-minimal' },
                { name: 'Featured Layout', description: 'One large featured item', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-featured' },
            ],
            hero: [
                { name: 'Split Right', description: 'Content on left, image on right', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split-right' },
                { name: 'Split Left', description: 'Image on left, content on right', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-split-left' },
                { name: 'Centered', description: 'Centered content with full-width image below', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
                { name: 'Full Background', description: 'Content overlaid on background image', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-full-bg' },
                { name: 'Asymmetric', description: 'Offset content with diagonal split', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-asymmetric' },
                { name: 'Minimal', description: 'Clean layout with minimal elements', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-minimal' },
                { name: 'Bold Typography', description: 'Large text-focused hero', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-bold-text' },
                { name: 'Video Background', description: 'Content over video background', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-video-bg' },
                { name: 'Split Diagonal', description: 'Diagonal split between content and image', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-diagonal' },
                { name: 'Stacked', description: 'Vertically stacked content and image', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-stacked' },
            ],
            features: [
                { name: '3-Column Grid', description: 'Three equal columns', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-3' },
                { name: '2-Column Grid', description: 'Two equal columns', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-grid-2' },
                { name: '4-Column Grid', description: 'Four equal columns', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-4' },
                { name: 'Horizontal Cards', description: 'Horizontally scrolling cards', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-horizontal' },
                { name: 'Staggered', description: 'Offset alternating cards', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-staggered' },
                { name: 'Masonry', description: 'Pinterest-style masonry layout', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-masonry' },
                { name: 'List View', description: 'Vertical list with icons', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Bento Grid', description: 'Mixed size grid layout', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-bento' },
                { name: 'Carousel', description: 'Sliding carousel of features', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-carousel' },
                { name: 'Tabs', description: 'Tabbed interface for features', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-tabs' },
            ],
            navbar: [
                { name: 'Classic Horizontal', description: 'Traditional horizontal navigation', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-horizontal' },
                { name: 'Centered Logo', description: 'Logo in center, links on sides', preview: this.generateLayoutPreview('navbar', 1), layoutClass: 'layout-centered-logo' },
                { name: 'Minimal', description: 'Clean minimal navigation', preview: this.generateLayoutPreview('navbar', 2), layoutClass: 'layout-minimal' },
                { name: 'Mega Menu', description: 'Dropdown mega menu', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-mega' },
                { name: 'Sidebar', description: 'Vertical sidebar navigation', preview: this.generateLayoutPreview('navbar', 1), layoutClass: 'layout-sidebar' },
                { name: 'Split', description: 'Logo left, actions right', preview: this.generateLayoutPreview('navbar', 2), layoutClass: 'layout-split' },
                { name: 'Transparent', description: 'Transparent overlay navigation', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-transparent' },
                { name: 'Sticky', description: 'Sticky header with scroll effect', preview: this.generateLayoutPreview('navbar', 1), layoutClass: 'layout-sticky' },
                { name: 'Hamburger', description: 'Mobile-first hamburger menu', preview: this.generateLayoutPreview('navbar', 2), layoutClass: 'layout-hamburger' },
                { name: 'Full Width', description: 'Full-width navigation bar', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-full-width' },
            ],
            testimonial: [
                { name: 'Carousel Slider', description: 'Sliding testimonial carousel', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-carousel' },
                { name: 'Grid 3-Column', description: 'Three testimonials in a row', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid-3' },
                { name: 'Featured Quote', description: 'Large centered testimonial', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-featured' },
                { name: 'Masonry Grid', description: 'Staggered testimonial cards', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-masonry' },
                { name: 'Video Testimonials', description: 'Video player grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-video-grid' },
                { name: 'Horizontal Scroll', description: 'Scrollable testimonial row', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-horizontal' },
                { name: 'Split Layout', description: 'Image and quote side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Card Stack', description: 'Stacked card design', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-stack' },
                { name: 'Minimal Quotes', description: 'Clean quote-focused layout', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-minimal' },
                { name: 'Wall of Love', description: 'Dense grid of testimonials', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-wall' },
            ],
            footer: [
                { name: 'Multi-Column', description: 'Multiple columns with links', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-multi-column' },
                { name: 'Centered Minimal', description: 'Centered simple footer', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
                { name: 'Newsletter Focus', description: 'Newsletter signup prominent', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-newsletter' },
                { name: 'Social First', description: 'Social media links emphasized', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-social' },
                { name: 'Mega Footer', description: 'Large footer with many sections', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-mega' },
                { name: 'Minimal Bar', description: 'Single line footer bar', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-bar' },
                { name: 'Split Footer', description: 'Logo left, links right', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Stacked', description: 'Vertically stacked sections', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-stacked' },
                { name: 'Grid Layout', description: 'Equal grid sections', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-grid' },
                { name: 'App Download', description: 'App store buttons prominent', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-app' },
            ],
            about: [
                { name: 'Story Timeline', description: 'Timeline of company history', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-timeline' },
                { name: 'Team Grid', description: 'Grid of team members', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-team-grid' },
                { name: 'Mission Statement', description: 'Large centered mission', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-mission' },
                { name: 'Split Content', description: 'Text and image side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Values Grid', description: 'Company values in grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-values' },
                { name: 'Founder Story', description: 'Founder-focused layout', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-founder' },
                { name: 'Stats Highlight', description: 'Key statistics prominent', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-stats' },
                { name: 'Culture Showcase', description: 'Company culture photos', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-culture' },
                { name: 'Milestone Cards', description: 'Achievement cards', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-milestones' },
                { name: 'Video Story', description: 'Video-centered about', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-video' },
            ],
            contact: [
                { name: 'Split Layout', description: 'Form and contact info side by side', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Centered Form', description: 'Centered contact form', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
                { name: 'Card Layout', description: 'Contact info in cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
                { name: 'List View', description: 'Vertical list of contact info', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
            ],
            pricing: [
                { name: '3-Tier Cards', description: 'Three pricing tiers', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-3-tier' },
                { name: 'Comparison Table', description: 'Feature comparison table', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-table' },
                { name: 'Toggle Monthly/Yearly', description: 'Billing toggle switch', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-toggle' },
                { name: 'Featured Plan', description: 'One plan highlighted', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-featured' },
                { name: 'Horizontal Scroll', description: 'Scrollable pricing cards', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-horizontal' },
                { name: 'Simple List', description: 'Vertical pricing list', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-list' },
                { name: 'Enterprise Focus', description: 'Enterprise plan prominent', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-enterprise' },
                { name: 'Calculator', description: 'Interactive price calculator', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-calculator' },
                { name: 'Tiered Features', description: 'Feature tiers emphasized', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-tiered' },
                { name: 'FAQ Included', description: 'Pricing with FAQ section', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-faq' },
            ],
            gallery: [
                { name: 'Masonry Grid', description: 'Pinterest-style masonry', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-masonry' },
                { name: 'Lightbox Carousel', description: 'Clickable image carousel', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-lightbox' },
                { name: 'Filterable Grid', description: 'Category filter grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-filterable' },
                { name: 'Full Width Slider', description: 'Full-width image slider', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-slider' },
                { name: 'Bento Layout', description: 'Mixed size bento grid', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-bento' },
                { name: 'Hover Overlay', description: 'Info on hover overlay', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-hover' },
                { name: 'Justified Grid', description: 'Justified row heights', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-justified' },
                { name: 'Polaroid Stack', description: 'Polaroid-style images', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-polaroid' },
                { name: 'Video Gallery', description: 'Video thumbnail grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-video' },
                { name: 'Infinite Scroll', description: 'Infinite scrolling grid', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-infinite' },
            ],
            blog: [
                { name: 'Card Grid', description: 'Blog post card grid', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-card-grid' },
                { name: 'List with Sidebar', description: 'List view with sidebar', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-list-sidebar' },
                { name: 'Featured Post', description: 'Large featured post', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-featured' },
                { name: 'Magazine Style', description: 'Magazine-style layout', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-magazine' },
                { name: 'Minimal List', description: 'Clean minimal list', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-minimal' },
                { name: 'Masonry Blog', description: 'Masonry blog cards', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-masonry' },
                { name: 'Timeline View', description: 'Chronological timeline', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-timeline' },
                { name: 'Category Tabs', description: 'Tabbed by category', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-tabs' },
                { name: 'Hero Posts', description: 'Large hero-style posts', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-hero' },
                { name: 'Compact Feed', description: 'Dense compact feed', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-compact' },
            ],
            stats: [
                { name: 'Counter Grid', description: 'Animated number counters', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-counter' },
                { name: 'Circular Progress', description: 'Circular progress bars', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-circular' },
                { name: 'Animated Numbers', description: 'Large animated stats', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-animated' },
                { name: 'Icon Stats', description: 'Stats with icons', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-icon-stats' },
                { name: 'Horizontal Bar', description: 'Horizontal stat bar', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-horizontal' },
                { name: 'Comparison Stats', description: 'Before/after comparison', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-comparison' },
                { name: 'Minimal Numbers', description: 'Clean number display', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-minimal' },
                { name: 'Chart Integration', description: 'Stats with charts', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-charts' },
                { name: 'Timeline Stats', description: 'Stats on timeline', preview: this.generateLayoutPreview('features', 2), layoutClass: 'layout-timeline' },
                { name: 'Card Stats', description: 'Stats in card format', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-cards' },
            ],
            cta: [
                { name: 'Centered Bold', description: 'Bold centered CTA', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-centered' },
                { name: 'Split with Image', description: 'CTA with side image', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-split' },
                { name: 'Banner Style', description: 'Full-width banner CTA', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-banner' },
                { name: 'Card CTA', description: 'CTA in card format', preview: this.generateLayoutPreview('features', 0), layoutClass: 'layout-card' },
                { name: 'Minimal CTA', description: 'Simple minimal CTA', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-minimal' },
                { name: 'Gradient Background', description: 'CTA with gradient', preview: this.generateLayoutPreview('hero', 1), layoutClass: 'layout-gradient' },
                { name: 'Video Background', description: 'CTA over video', preview: this.generateLayoutPreview('hero', 0), layoutClass: 'layout-video' },
                { name: 'Multi-Button', description: 'Multiple CTA options', preview: this.generateLayoutPreview('features', 1), layoutClass: 'layout-multi' },
                { name: 'Sticky Bottom', description: 'Sticky bottom CTA bar', preview: this.generateLayoutPreview('navbar', 0), layoutClass: 'layout-sticky' },
                { name: 'Popup Style', description: 'Modal-style CTA', preview: this.generateLayoutPreview('hero', 2), layoutClass: 'layout-popup' },
            ]
        };

        return fallbacks[sectionType] || fallbacks.hero;
    }

    applyLayoutOption(layout) {
        if (!this.activeSection) return;

        const { element, pageId, index, section } = this.activeSection;

        // Update section with new layout class
        section.layoutVariant = layout.layoutClass;
        section.layoutName = layout.name;

        // Re-render the section content with new layout
        const content = this.createSectionContent(section, index, pageId);
        const oldContent = element.querySelector('.section-content');
        if (oldContent) {
            oldContent.replaceWith(content);
        }

        // Re-bind events to the updated section
        this.bindSectionEvents(element, section, index, pageId);

        // Save to state
        if (window.stateManager) {
            window.stateManager.updateSection(pageId, index, {
                layoutVariant: layout.layoutClass,
                layoutName: layout.name
            });
        }

        // DON'T close sidebar - keep it open for trying more layouts
        // this.closeSidebar();

        // Show success message
        this.showNotification(`Layout changed to "${layout.name}"`);
    }

    showNotification(message) {
        // Simple notification
        const notification = document.createElement('div');
        notification.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:12px 20px;border-radius:8px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.15);';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    openSectionSuggestions(section, index, pageId, element) {
        // Activate section
        if (this.activeSection && this.activeSection.element) {
            this.activeSection.element.classList.remove('selected');
        }
        this.activeSection = { section, index, pageId, element };
        element.classList.add('selected');

        // Open sidebar and populate suggestions
        const sidebar = document.getElementById('sectionSettingsSidebar');
        const replaceView = document.getElementById('sidebarReplaceView');
        const nameSpan = document.getElementById('suggestionSectionName');
        if (nameSpan) nameSpan.textContent = `Suggestions for ${section.type.charAt(0).toUpperCase() + section.type.slice(1)}`;
        if (sidebar) sidebar.classList.add('active');
        if (replaceView) replaceView.classList.add('active');
        const list = document.getElementById('suggestionList');
        if (list) {
            const suggestions = this.getAISuggestions(section.type);
            list.innerHTML = suggestions.map((s, i) => `
                <div class="suggestion-card" data-idx="${i}">
                    <div class="suggestion-preview" style="background:${s.styles.backgroundColor}; color:${s.styles.textColor}">
                        <div style="text-align:center;">
                            <div style="font-weight:700; margin-bottom:6px;">${s.title}</div>
                            <div style="font-size:12px;">${s.subtitle}</div>
                            <div style="margin-top:8px;">
                                <span style="display:inline-block; padding:6px 12px; border-radius:6px; background:${s.styles.btnColor}; color:${s.styles.btnTextColor}; font-size:12px;">${s.cta}</span>
                            </div>
                        </div>
                    </div>
                    <div class="suggestion-meta">
                        Layout: ${s.layout === 'alt' ? 'Alternate' : 'Default'} • Palette
                    </div>
                </div>
            `).join('');
            list.querySelectorAll('.suggestion-card').forEach(card => {
                card.addEventListener('click', () => {
                    const idx = parseInt(card.dataset.idx, 10);
                    const chosen = suggestions[idx];
                    this.applySuggestion(chosen);
                });
            });
        }
    }

    getAISuggestions(type) {
        // AI Suggestion Engine: Generates unique, high-quality UI/UX design themes
        const themes = [
            {
                name: 'Modern Minimalist',
                layout: 'default',
                styles: {
                    textColor: '#1a1a1b',
                    backgroundColor: '#ffffff',
                    btnColor: '#007aff',
                    btnTextColor: '#ffffff',
                    headingFont: "'Inter', sans-serif",
                    paragraphFont: "'Inter', sans-serif"
                },
                title: 'Clean & Impactful Hero',
                subtitle: 'Two-column minimalist layout with focus on white space and bold serenity.',
                cta: 'Get Started'
            },
            {
                name: 'Creative Mesh',
                layout: 'alt',
                styles: {
                    textColor: '#ffffff',
                    backgroundColor: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                    btnColor: '#ffffff',
                    btnTextColor: '#6366f1',
                    headingFont: "'Montserrat', sans-serif",
                    paragraphFont: "'Poppins', sans-serif"
                },
                title: 'Immersive Experience',
                subtitle: 'Vibrant mesh gradient with centered content and floating glassmorphism elements.',
                cta: 'Explore More'
            },
            {
                name: 'Future Tech',
                layout: 'default',
                styles: {
                    textColor: '#10b981',
                    backgroundColor: '#050816',
                    btnColor: '#10b981',
                    btnTextColor: '#050816',
                    headingFont: "'Roboto Mono', monospace",
                    paragraphFont: "'Roboto', sans-serif"
                },
                title: 'Next-Gen Interface',
                subtitle: 'Electric glow on dark mode. Sharp edges and high-tech monospaced accents.',
                cta: 'Deploy Now'
            },
            {
                name: 'Editorial Offset',
                layout: 'alt',
                styles: {
                    textColor: '#556b2f',
                    backgroundColor: '#fdfcfb',
                    btnColor: '#556b2f',
                    btnTextColor: '#fdfcfb',
                    headingFont: "'Playfair Display', serif",
                    paragraphFont: "'Georgia', serif"
                },
                title: 'The Editorial Story',
                subtitle: 'High-end magazine aesthetic with offset typography and elegant serif pairings.',
                cta: 'Read Story'
            },
            {
                name: 'Dynamic Bento',
                layout: 'default',
                styles: {
                    textColor: '#1f2937',
                    backgroundColor: '#f3f4f6',
                    btnColor: '#111827',
                    btnTextColor: '#ffffff',
                    headingFont: "'Public Sans', sans-serif",
                    paragraphFont: "'Public Sans', sans-serif"
                },
                title: 'Bento Grid Layout',
                subtitle: 'Modular card-based design perfect for modern SaaS and application homepages.',
                cta: 'View Dashboard'
            }
        ];

        // Specific content mapping based on section type
        const typeLabels = {
            hero: { suffix: 'Headline', desc: 'Powerful hero section for maximum conversion' },
            features: { suffix: 'Showcase', desc: 'Detail your value propositions in a structured way' },
            navbar: { suffix: 'Navigation', desc: 'Seamless and intuitive site architecture' },
            testimonial: { suffix: 'Social Proof', desc: 'Build trust with verified customer feedback' }
        };

        const config = typeLabels[type] || { suffix: 'Variant', desc: 'Alternative layout for this section' };

        return themes.map(theme => ({
            ...theme,
            title: `${theme.name} ${config.suffix}`,
            subtitle: config.desc
        }));
    }

    applySuggestion(suggestion) {
        if (!this.activeSection) return;
        const { element, pageId, index } = this.activeSection;
        // apply styles live
        const styles = { ...(this.activeSection.section.styles || {}), ...suggestion.styles };
        this.activeSection.section.styles = styles;
        this.applyStylesToElement(element, styles);
        // layout toggle
        const contentDiv = element.querySelector('.wireframe-element') || element.querySelector('.section-content > div');
        if (contentDiv) {
            const shouldAlt = suggestion.layout === 'alt';
            contentDiv.classList.toggle('layout-alt', shouldAlt);
        }
        // persist
        this.saveStyles(styles);
        // close sidebar
        const sidebar = document.getElementById('sectionSettingsSidebar');
        if (sidebar) sidebar.classList.remove('active');
    }

    // Make text editable
    // Make text editable
    makeTextEditable(textEl, pageId, index) {
        const currentText = (textEl.textContent || '').trim();
        const field = textEl.dataset.field;
        const itemIndex = textEl.dataset.index;

        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentText;
        input.className = 'inline-editor';

        textEl.replaceWith(input);
        input.focus();
        input.select();

        const saveEdit = () => {
            const newText = input.value;
            textEl.textContent = newText;
            input.replaceWith(textEl);

            // Update state
            if (window.stateManager) {
                if (itemIndex !== undefined && this.activeSection && this.activeSection.section.items) {
                    const items = JSON.parse(JSON.stringify(this.activeSection.section.items));
                    const idx = parseInt(itemIndex);
                    if (items[idx]) {
                        if (field === 'item-title') items[idx].title = newText;
                        if (field === 'item-desc') items[idx].desc = newText;
                        this.handleContentChange('items', items);
                    }
                } else if (field) {
                    this.handleContentChange(field, newText);
                }
            }
        };

        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') saveEdit();
            else if (e.key === 'Escape') input.replaceWith(textEl);
        });
    }

    handleContentChange(field, value) {
        if (this.activeSection) {
            const updates = {};
            updates[field] = value;
            this.activeSection.section[field] = value;
            window.stateManager.updateSection(this.activeSection.pageId, this.activeSection.index, updates);
        }
    }

    syncSectionData(section) {
        if (window.stateManager && section.pageId !== undefined) {
            window.stateManager.updateSection(section.pageId, section.index, section);
        }
    }

    createContactWireframe(section, variant) {
        const items = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { icon: this.getSectionFallbackVisual('contact', 0).emoji, title: 'Address', desc: '123 Business St, Suite 100, City, State 12345' },
            { icon: this.getSectionFallbackVisual('contact', 1).emoji, title: 'Email', desc: 'contact@company.com' },
            { icon: this.getSectionFallbackVisual('contact', 2).emoji, title: 'Phone', desc: '+1 (555) 123-4567' },
            { icon: this.getSectionFallbackVisual('contact', 3).emoji, title: 'Hours', desc: 'Mon-Fri, 9AM-6PM' }
        ]).slice(0, 4);
        const cards = items.map(item => `
            <div style="padding: 20px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                <div style="font-size: 24px; margin-bottom: 10px;">${item.icon || this.getSectionFallbackVisual('contact').emoji}</div>
                <div style="font-weight: 600; margin-bottom: 8px; color: #1e293b;">${item.title || 'Contact'}</div>
                <div style="font-size: 14px; color: #64748b; line-height: 1.6;">${item.desc || ''}</div>
            </div>
        `).join('');

        if (variant === 'layout-centered' || variant === 'layout-minimal' || variant === 'layout-list') {
            return `
                <div style="max-width: 760px; margin: 40px auto;">
                    <div style="text-align: center; margin-bottom: 32px;">
                        <h3 class="editable-text" data-field="title" style="font-size: 32px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">${section.title || 'Get in Touch'}</h3>
                        <p class="editable-text" data-field="description" style="font-size: 16px; color: #64748b;">${section.description || this.getTitleAwareFallbackText(section.title || 'contact', 'contact')}</p>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">${cards}</div>
                </div>
            `;
        }

        if (variant === 'layout-map-large') {
            return `
                <div style="margin-top: 24px;">
                    <div style="height: 400px; background: #e2e8f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 18px; margin-bottom: 32px;">
                        ${section.mapLabel || 'Map / Location'}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">${cards}</div>
                </div>
            `;
        }

        return `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 24px;">
                <div>
                    <div style="margin-bottom: 18px;"><label style="display:block;font-weight:500;margin-bottom:8px;font-size:14px;">Name</label><div style="height:40px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"></div></div>
                    <div style="margin-bottom: 18px;"><label style="display:block;font-weight:500;margin-bottom:8px;font-size:14px;">Email</label><div style="height:40px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"></div></div>
                    <div style="margin-bottom: 18px;"><label style="display:block;font-weight:500;margin-bottom:8px;font-size:14px;">Message</label><div style="height:120px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"></div></div>
                    <button style="width:100%;padding:12px;background:#6366f1;color:white;border:none;border-radius:6px;font-weight:500;cursor:pointer;">${section.buttonText || 'Send Message'}</button>
                </div>
                <div>
                    <h3 class="editable-text" data-field="title" style="font-size: 28px; font-weight: 700; margin-bottom: 12px; color: #1e293b;">${section.title || 'Get in Touch'}</h3>
                    <p class="editable-text" data-field="description" style="font-size: 15px; color: #64748b; margin-bottom: 20px;">${section.description || this.getTitleAwareFallbackText(section.title || 'contact', 'contact')}</p>
                    <div style="display:grid;gap:16px;">${cards}</div>
                    <div style="height:200px;background:#e2e8f0;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#94a3b8;margin-top:24px;">${section.mapLabel || 'Map'}</div>
                </div>
            </div>
        `;
    }

    createContactFormWireframe(section, variant) {
        const formTitle = section.title || 'Contact Us';
        const formDesc = section.description || this.getTitleAwareFallbackText(section.title || 'contact form', 'form');
        const fields = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Full Name' }, { title: 'Email Address' }, { title: 'Subject' }, { title: 'Message' }
        ]);
        return `
            <div style="max-width: 600px; margin: 40px auto; padding: 32px; background: white; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h3 class="editable-text" data-field="title" style="font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">${formTitle}</h3>
                    <p class="editable-text" data-field="description" style="color: #64748b;">${formDesc}</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    ${fields.map((field, i) => `
                        <div>
                            <label class="editable-text" data-field="item-title" data-index="${i}" style="display: block; font-weight: 500; margin-bottom: 6px; color: #334155;">${field.title || `Field ${i + 1}`}</label>
                            <div style="height: ${/message/i.test(field.title || '') ? '120px' : '42px'}; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;"></div>
                        </div>
                    `).join('')}
                    <button style="margin-top: 8px; width: 100%; padding: 12px; background: #6366f1; color: white; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;">${section.buttonText || 'Send Message'}</button>
                </div>
            </div>
        `;
    }

    createPricingWireframe(section, variant) {
        const plans = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Basic', price: '$9', desc: 'Feature 1, Feature 2, Feature 3' },
            { title: 'Pro', price: '$29', desc: 'All Basic, Feature 4, Feature 5, Feature 6', tag: 'POPULAR' },
            { title: 'Enterprise', price: '$99', desc: 'All Pro, Feature 7, Feature 8, Priority Support' }
        ]).map(plan => ({
            title: plan.title || 'Plan',
            price: plan.price || '$0',
            features: Array.isArray(plan.items) && plan.items.length > 0 ? plan.items : String(plan.desc || '').split(/,|\n/).map(p => p.trim()).filter(Boolean),
            tag: plan.tag || '',
            desc: plan.desc || plan.description || '',
        }));
        const header = `
            <div style="text-align:center;max-width:760px;margin:0 auto 28px;">
                <h2 class="editable-text" data-field="title" style="font-size:32px;font-weight:700;margin-bottom:12px;color:#1e293b;">${section.title || 'Pricing'}</h2>
                <p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;">${section.description || ''}</p>
            </div>
        `;

        if (variant === 'layout-table') {
            return `
                ${header}
                <div style="margin-top: 24px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead><tr style="background:#f8fafc;"><th style="padding:16px;text-align:left;">Plan</th>${plans.map(p => `<th style="padding:16px;text-align:center;">${p.title}</th>`).join('')}</tr></thead>
                        <tbody><tr><td style="padding:12px;border-top:1px solid #e2e8f0;">Price</td>${plans.map(p => `<td style="padding:12px;text-align:center;border-top:1px solid #e2e8f0;font-weight:700;color:#6366f1;">${p.price}</td>`).join('')}</tr></tbody>
                    </table>
                </div>
            `;
        }

        const gridStyle = variant === 'layout-horizontal' ? 'display:flex;gap:24px;overflow-x:auto;padding-bottom:16px;' : 'display:grid;grid-template-columns:repeat(3, 1fr);gap:24px;';
        return `
            ${header}
            <div class="pricing-grid" style="${gridStyle} margin-top:24px;">
                ${plans.map(plan => `
                    <div class="pricing-card" style="min-width:300px;background:white;border:2px solid ${plan.tag ? '#6366f1' : '#e2e8f0'};border-radius:12px;padding:32px;position:relative;">
                        ${plan.tag ? `<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#6366f1;color:white;padding:4px 16px;border-radius:12px;font-size:12px;font-weight:600;">${plan.tag}</div>` : ''}
                        <div style="font-size:20px;font-weight:700;margin-bottom:8px;">${plan.title}</div>
                        <p style="font-size:14px;color:#64748b;margin-bottom:12px;">${plan.desc}</p>
                        <div style="font-size:36px;font-weight:800;color:#6366f1;margin-bottom:16px;">${plan.price}</div>
                        <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:24px;">
                            ${plan.features.map(f => `<div style="font-size:14px;color:#64748b;">• ${f}</div>`).join('')}
                        </div>
                        <button style="width:100%;padding:12px;background:${plan.tag ? '#6366f1' : 'white'};color:${plan.tag ? 'white' : '#6366f1'};border:2px solid #6366f1;border-radius:6px;font-weight:600;cursor:pointer;">${section.buttonText || 'Get Started'}</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createGalleryWireframe(section, variant) {
        const items = (Array.isArray(section.items) && section.items.length > 0 ? section.items : Array.from({ length: 6 }, (_, i) => ({ title: `Image ${i + 1}` })));
        const cols = variant === 'layout-grid-2' ? 2 : variant === 'layout-grid-4' ? 4 : 3;
        const wrapper = variant === 'layout-horizontal'
            ? `display:flex;gap:16px;overflow-x:auto;margin-top:24px;padding-bottom:16px;`
            : `display:grid;grid-template-columns:repeat(${cols}, 1fr);gap:16px;margin-top:24px;`;
        return `
            <div style="${wrapper}">
                ${items.map((item, i) => `
                    <div class="gallery-item" style="${variant === 'layout-horizontal' ? 'min-width:300px;' : ''} aspect-ratio:${variant === 'layout-grid-4' ? '1' : '4/3'}; background:#e2e8f0; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#94a3b8; font-size:14px;">
                        <span class="editable-text" data-field="item-title" data-index="${i}">${item.title || `Image ${i + 1}`}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createBlogWireframe(section, variant) {
        const posts = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { title: 'Getting Started Guide', desc: 'Learn the basics and get up to speed quickly...', tag: 'Jan 15, 2024' },
            { title: 'Advanced Tips & Tricks', desc: 'Take your skills to the next level with these...', tag: 'Jan 10, 2024' },
            { title: 'Best Practices', desc: 'Follow these guidelines for optimal results...', tag: 'Jan 5, 2024' }
        ]);
        const header = `
            <div style="text-align:center;max-width:760px;margin:0 auto 28px;">
                <h2 class="editable-text" data-field="title" style="font-size:32px;font-weight:700;margin-bottom:12px;color:#1e293b;">${section.title || 'Latest Posts'}</h2>
                <p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;">${section.description || ''}</p>
            </div>
        `;

        if (variant === 'layout-featured') {
            const featured = posts[0];
            const rest = posts.slice(1);
            return `
                ${header}
                <div style="margin-top:24px;">
                    <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:32px;">
                        <div style="height:300px;background:#e2e8f0;display:flex;align-items:center;justify-content:center;color:#94a3b8;">Featured Image</div>
                        <div style="padding:32px;">
                            <div style="font-size:12px;color:#94a3b8;margin-bottom:12px;">${featured.tag || ''}</div>
                            <div class="editable-text" data-field="item-title" data-index="0" style="font-size:28px;font-weight:700;margin-bottom:16px;">${featured.title || ''}</div>
                            <p class="editable-text" data-field="item-desc" data-index="0" style="font-size:16px;color:#64748b;">${featured.desc || ''}</p>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:24px;">
                        ${rest.map((post, i) => `
                            <div style="background:white;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
                                <div style="height:150px;background:#e2e8f0;display:flex;align-items:center;justify-content:center;color:#94a3b8;">Image</div>
                                <div style="padding:20px;">
                                    <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">${post.tag || ''}</div>
                                    <div class="editable-text" data-field="item-title" data-index="${i + 1}" style="font-size:16px;font-weight:600;margin-bottom:8px;">${post.title || ''}</div>
                                    <p class="editable-text" data-field="item-desc" data-index="${i + 1}" style="font-size:14px;color:#64748b;">${post.desc || ''}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        return `
            ${header}
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:24px;">
                ${posts.map((post, i) => `
                    <div class="blog-card" style="background:white;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
                        <div style="height:180px;background:#e2e8f0;display:flex;align-items:center;justify-content:center;color:#94a3b8;">Featured Image</div>
                        <div style="padding:20px;">
                            <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">${post.tag || ''}</div>
                            <div class="editable-text" data-field="item-title" data-index="${i}" style="font-size:18px;font-weight:600;margin-bottom:8px;">${post.title || ''}</div>
                            <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size:14px;color:#64748b;">${post.desc || ''}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createServicesWireframe(section, variant) {
        const services = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { icon: this.getSectionFallbackVisual('services', 0).emoji, title: 'Strategy', desc: 'Comprehensive planning and execution' },
            { icon: this.getSectionFallbackVisual('services', 1).emoji, title: 'Innovation', desc: 'Cutting-edge solutions for your needs' },
            { icon: this.getSectionFallbackVisual('services', 2).emoji, title: 'Growth', desc: 'Scale your business effectively' }
        ]);
        const wrapper = variant === 'layout-list'
            ? 'display:flex;flex-direction:column;gap:24px;'
            : variant === 'layout-horizontal'
                ? 'display:flex;gap:24px;overflow-x:auto;padding-bottom:16px;'
                : 'display:grid;grid-template-columns:repeat(auto-fit, minmax(250px, 1fr));gap:24px;';
        return `
            <div style="text-align:center;max-width:760px;margin:0 auto 28px;">
                <h2 class="editable-text" data-field="title" style="font-size:32px;font-weight:700;margin-bottom:12px;color:#1e293b;">${section.title || 'Services'}</h2>
                <p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;">${section.description || ''}</p>
            </div>
            <div style="${wrapper} margin-top:24px;width:100%;">
                ${services.map((s, i) => `
                    <div style="${variant === 'layout-horizontal' ? 'min-width:280px;' : ''} background:${variant === 'layout-featured' && i === 0 ? 'linear-gradient(135deg, #6366f1, #a855f7)' : '#f8fafc'}; color:${variant === 'layout-featured' && i === 0 ? 'white' : 'inherit'}; padding:32px; border-radius:12px; border:1px solid #e2e8f0; box-sizing:border-box;">
                        <div style="font-size:48px;margin-bottom:16px;">${s.icon || this.getSectionFallbackVisual('services', i).emoji}</div>
                        <h3 class="editable-text" data-field="item-title" data-index="${i}" style="font-size:20px;font-weight:600;margin-bottom:12px;word-wrap:break-word;">${s.title || `Service ${i + 1}`}</h3>
                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size:15px;line-height:1.6;word-wrap:break-word;">${s.desc || s.description || ''}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createInformationWireframe(section, variant) {
        const items = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { icon: this.getSectionFallbackVisual('information', 0).emoji, title: 'Analytics', desc: 'Comprehensive information and insights.' },
            { icon: this.getSectionFallbackVisual('information', 1).emoji, title: 'Security', desc: 'Protection, reliability, and governance.' },
            { icon: this.getSectionFallbackVisual('information', 2).emoji, title: 'Performance', desc: 'Operational speed and efficiency gains.' }
        ]);
        const wrapper = variant === 'layout-list'
            ? 'display:flex;flex-direction:column;gap:20px;max-width:700px;margin:0 auto;'
            : 'display:grid;grid-template-columns:repeat(auto-fit, minmax(250px, 1fr));gap:24px;';
        return `
            <div style="text-align:center;max-width:760px;margin:0 auto 28px;">
                <h2 class="editable-text" data-field="title" style="font-size:32px;font-weight:700;margin-bottom:12px;color:#1e293b;">${section.title || 'Information'}</h2>
                <p class="editable-text" data-field="description" style="font-size:16px;color:#64748b;line-height:1.7;">${section.description || ''}</p>
            </div>
            <div style="${wrapper} margin-top:24px;width:100%;">
                ${items.map((item, i) => `
                    <div style="background:${variant === 'layout-list' ? 'transparent' : (variant === 'layout-grid' ? 'white' : '#f8fafc')};padding:${variant === 'layout-list' ? '24px 0' : '32px'};border-radius:12px;${variant === 'layout-list' ? (i < items.length - 1 ? 'border-bottom:1px solid #e2e8f0;' : '') : 'border:1px solid #e2e8f0;'} box-sizing:border-box;">
                        <div style="font-size:40px;margin-bottom:16px;">${item.icon || this.getSectionFallbackVisual('information', i).emoji}</div>
                        <h3 class="editable-text" data-field="item-title" data-index="${i}" style="font-size:20px;font-weight:600;margin-bottom:12px;color:#1e293b;">${item.title || ''}</h3>
                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size:14px;color:#64748b;line-height:1.6;">${item.desc || item.description || ''}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createContactDetailsWireframe(section, variant) {
        const items = (Array.isArray(section.items) && section.items.length > 0 ? section.items : [
            { icon: this.getSectionFallbackVisual('contact', 0).emoji, title: 'Phone', desc: '+1 (555) 123-4567' },
            { icon: this.getSectionFallbackVisual('contact', 1).emoji, title: 'Email', desc: 'hello@company.com' },
            { icon: this.getSectionFallbackVisual('contact', 2).emoji, title: 'Live Chat', desc: 'Available 24/7' },
            { icon: this.getSectionFallbackVisual('contact', 3).emoji, title: 'Hours', desc: 'Mon-Fri 9AM-6PM' }
        ]);
        const wrapper = variant === 'layout-list' || variant === 'layout-minimal'
            ? 'max-width:600px;margin:0 auto;display:flex;flex-direction:column;'
            : 'display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:24px;';
        return `
            <div style="${wrapper} margin-top:24px;width:100%;">
                ${items.map((item, i) => `
                    <div style="padding:24px;${variant === 'layout-list' || variant === 'layout-minimal' ? (i < items.length - 1 ? 'border-bottom:1px solid #e2e8f0;' : '') : 'background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;'} box-sizing:border-box;">
                        <div style="font-size:24px;margin-bottom:10px;">${item.icon || this.getSectionFallbackVisual('contact', i).emoji}</div>
                        <div class="editable-text" data-field="item-title" data-index="${i}" style="font-size:18px;font-weight:600;margin-bottom:8px;color:#1e293b;">${item.title || ''}</div>
                        <p class="editable-text" data-field="item-desc" data-index="${i}" style="font-size:15px;color:#64748b;line-height:1.6;">${item.desc || ''}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    ensureHeroContent(section) {
        const title = (section.title || '').toLowerCase();
        if (!section.title || title.includes('hero') || title.includes('header') || title.includes('section')) {
            section.title = section.title || "Build trust from the first screen";
            section.description = section.description || "Clarify your value proposition with confident, benefit-led messaging generated from the API.";
            section.buttonText = section.buttonText || "Explore More";
            this.syncSectionData(section);
        }
    }

    // Delete section from wireframe (syncs to sitemap)
    deleteSection(pageId, index) {
        if (confirm('Delete this section?')) {
            if (window.stateManager) {
                window.stateManager.deleteSection(pageId, index);
            }
        }
    }

    // Create empty state
    createEmptyState(pageId) {
        const emptyState = document.createElement('div');
        emptyState.className = 'wireframe-empty-state';
        emptyState.innerHTML = `
            <div class="empty-content">
                <h3>No sections yet</h3>
                <p>Add sections from the Sitemap view to see them here</p>
            </div>
        `;
        return emptyState;
    }

    // State sync event handlers
    onSectionAdded(data) {
        this.refreshPageColumn(data.pageId);
    }

    onSectionUpdated(data) {
        const column = document.querySelector(`.wireframe-page-column[data-page-id="${data.pageId}"]`);
        if (column) {
            const sectionEl = column.querySelector(`[data-section-index="${data.sectionIndex}"]`);
            if (sectionEl) {
                const newContent = this.createSectionContent(data.section, data.sectionIndex, data.pageId);
                const oldContent = sectionEl.querySelector('.section-content');
                if (oldContent) {
                    oldContent.replaceWith(newContent);
                    this.bindSectionEvents(sectionEl, data.section, data.sectionIndex, data.pageId);
                    if (data.section.styles) {
                        const s = data.section.styles;
                        this.applyStylesToElement(sectionEl, s);
                        if (s.headingFont || s.paragraphFont) {
                            if (s.headingFont) {
                                sectionEl.querySelectorAll('h1,h2,h3,.hero-wireframe h1,.features-wireframe h2,.navbar-wireframe .nav-logo span').forEach(node => {
                                    node.style.fontFamily = s.headingFont;
                                });
                            }
                            if (s.paragraphFont) {
                                sectionEl.querySelectorAll('p,.hero-wireframe p,.features-wireframe p,.navbar-wireframe .nav-link').forEach(node => {
                                    node.style.fontFamily = s.paragraphFont;
                                });
                            }
                        }
                    }
                    return;
                }
            }
        }
        this.refreshPageColumn(data.pageId);
    }

    onSectionDeleted(data) {
        this.refreshPageColumn(data.pageId);
    }

    onSitemapUpdated(sitemap) {
        this.renderAllPages(sitemap);
        if (window.sitemapApp) {
            window.sitemapApp.updateJsonDisplay();
        }
    }

    initializeAccordions() {
        if (!this.accordionHandlers) {
            this.accordionHandlers = new Map();
        }
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        accordionHeaders.forEach(header => {
            const oldHandler = this.accordionHandlers.get(header);
            if (oldHandler) header.removeEventListener('click', oldHandler);
            const newHandler = (e) => {
                e.stopPropagation();
                header.parentElement.classList.toggle('open');
            };
            this.accordionHandlers.set(header, newHandler);
            header.addEventListener('click', newHandler);
        });
    }

    initializeSidebarTabs() {
        if (!this.tabHandlers) {
            this.tabHandlers = new Map();
        }
        const tabs = document.querySelectorAll('.sidebar-tab');
        tabs.forEach(tab => {
            const oldHandler = this.tabHandlers.get(tab);
            if (oldHandler) tab.removeEventListener('click', oldHandler);
            const newHandler = (e) => {
                e.stopPropagation();
                const targetTab = tab.dataset.tab;
                document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                const targetPane = document.getElementById(`tab-${targetTab}`);
                if (targetPane) targetPane.classList.add('active');
            };
            this.tabHandlers.set(tab, newHandler);
            tab.addEventListener('click', newHandler);
        });
    }
}

// Do not auto-instantiate here; initialization is handled in wireframe.html

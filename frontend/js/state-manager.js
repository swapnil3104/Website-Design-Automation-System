// Global State Manager for Sitemap ↔ Wireframe Synchronization
class StateManager {
    constructor() {
        this.sitemap = null;
        this.listeners = new Map();
        this.eventId = 0;
    }

    // Set the entire sitemap
    setSitemap(sitemap) {
        // CRITICAL SAFEGUARD: Deduplicate pages before storing
        if (sitemap && sitemap.pages && Array.isArray(sitemap.pages)) {
            const seenIds = new Set();
            const uniquePages = [];

            sitemap.pages.forEach(page => {
                if (page.id && !seenIds.has(page.id)) {
                    seenIds.add(page.id);
                    uniquePages.push(page);
                }
            });

            if (uniquePages.length !== sitemap.pages.length) {
                console.warn(`🛡️ StateManager: Prevented ${sitemap.pages.length - uniquePages.length} duplicate page(s) from being stored`);
                sitemap.pages = uniquePages;
            }
        }

        this.sitemap = sitemap;
        this.notifyListeners('sitemap:updated', sitemap);
    }

    // Alias for compatibility
    setState(sitemap) {
        this.setSitemap(sitemap);
    }

    // Get the entire sitemap
    getSitemap() {
        return this.sitemap;
    }

    // Alias for compatibility
    getState() {
        return this.getSitemap();
    }

    // Find a page by ID
    findPageById(pageId) {
        if (!this.sitemap || !this.sitemap.pages) return null;
        return this.sitemap.pages.find(p => p.id === pageId);
    }

    // Update a specific page
    updatePage(pageId, updatedPage) {
        if (!this.sitemap || !this.sitemap.pages) return;
        const index = this.sitemap.pages.findIndex(p => p.id === pageId);
        if (index !== -1) {
            this.sitemap.pages[index] = { ...this.sitemap.pages[index], ...updatedPage };
            this.notifyListeners('sitemap:updated', this.sitemap);
        }
    }

    // Add a section to a page
    addSection(pageId, section) {
        const page = this.findPageById(pageId);
        if (page) {
            if (!page.sections) page.sections = [];
            page.sections.push(section);
            this.notifyListeners('section:added', { pageId, section });
            this.notifyListeners('sitemap:updated', this.sitemap);
        }
    }

    // Update a section
    updateSection(pageId, sectionIndex, updatedSection) {
        const page = this.findPageById(pageId);
        if (page && page.sections && page.sections[sectionIndex]) {
            page.sections[sectionIndex] = { ...page.sections[sectionIndex], ...updatedSection };
            this.notifyListeners('section:updated', { pageId, sectionIndex, section: page.sections[sectionIndex] });
            this.notifyListeners('sitemap:updated', this.sitemap);
        }
    }

    // Delete a section
    deleteSection(pageId, sectionIndex) {
        const page = this.findPageById(pageId);
        if (page && page.sections) {
            page.sections.splice(sectionIndex, 1);
            this.notifyListeners('section:deleted', { pageId, sectionIndex });
            this.notifyListeners('sitemap:updated', this.sitemap);
        }
    }

    // Event system
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Map());
        }
        const id = this.eventId++;
        this.listeners.get(event).set(id, callback);
        return id;
    }

    removeEventListener(event, id) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).delete(id);
        }
    }

    notifyListeners(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }

    // Alias for addEventListener
    on(event, callback) {
        return this.addEventListener(event, callback);
    }

    // Alias for removeEventListener
    off(event, id) {
        this.removeEventListener(event, id);
    }

    // Alias for notifyListeners
    dispatch(event, data) {
        this.notifyListeners(event, data);
    }

    // Save to localStorage
    saveToLocalStorage() {
        if (this.sitemap) {
            localStorage.setItem('currentSitemap', JSON.stringify(this.sitemap));
        }
    }
}

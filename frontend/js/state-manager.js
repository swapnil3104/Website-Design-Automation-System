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
        this.saveToLocalStorage();
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
        return this.sitemap.pages.find(p => String(p.id) === String(pageId));
    }

    // Update a specific page
    updatePage(pageId, updatedPage) {
        if (!this.sitemap || !this.sitemap.pages) return;
        const index = this.sitemap.pages.findIndex(p => String(p.id) === String(pageId));
        if (index !== -1) {
            this.sitemap.pages[index] = { ...this.sitemap.pages[index], ...updatedPage };
            this.saveToLocalStorage();
            this.notifyListeners('page:updated', { pageId, page: this.sitemap.pages[index] });
            this.notifyListeners('sitemap:updated', this.sitemap);
        }
    }

    // Add a section to a page (optionally at a specific index)
    addSection(pageId, section, atIndex = null) {
        const page = this.findPageById(pageId);
        if (page) {
            if (!page.sections) page.sections = [];
            const insertIndex = (atIndex !== null && atIndex >= 0 && atIndex <= page.sections.length)
                ? atIndex
                : page.sections.length;
            page.sections.splice(insertIndex, 0, section);
            this.saveToLocalStorage();
            this.notifyListeners('section:added', { pageId, section, index: insertIndex });
            this.notifyListeners('sitemap:updated', this.sitemap);
            return true;
        }
        return false;
    }

    // Update a section
    updateSection(pageId, sectionIndex, updatedSection) {
        const page = this.findPageById(pageId);
        if (page && page.sections && page.sections[sectionIndex]) {
            page.sections[sectionIndex] = { ...page.sections[sectionIndex], ...updatedSection };
            this.saveToLocalStorage();
            this.notifyListeners('section:updated', { pageId, sectionIndex, section: page.sections[sectionIndex] });
            this.notifyListeners('sitemap:updated', this.sitemap);
            return true;
        }
        return false;
    }

    // Reorder sections within a page
    reorderSections(pageId, fromIndex, toIndex) {
        const page = this.findPageById(pageId);
        if (page && page.sections && Array.isArray(page.sections)) {
            if (fromIndex >= 0 && fromIndex < page.sections.length && toIndex >= 0 && toIndex < page.sections.length) {
                const [movedSection] = page.sections.splice(fromIndex, 1);
                page.sections.splice(toIndex, 0, movedSection);
                this.saveToLocalStorage();
                this.notifyListeners('section:reordered', { pageId, fromIndex, toIndex, sections: page.sections });
                this.notifyListeners('sitemap:updated', this.sitemap);
                return true;
            }
        }
        return false;
    }

    // Delete a section
    deleteSection(pageId, sectionIndex) {
        const page = this.findPageById(pageId);
        if (page && page.sections && sectionIndex >= 0 && sectionIndex < page.sections.length) {
            const [deletedSection] = page.sections.splice(sectionIndex, 1);
            this.saveToLocalStorage();
            this.notifyListeners('section:deleted', { pageId, sectionIndex, section: deletedSection });
            this.notifyListeners('sitemap:updated', this.sitemap);
            return true;
        }
        return false;
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
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (err) {
                    console.error(`Error in stateManager listener for ${event}:`, err);
                }
            });
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

    // Save to localStorage safely (runs in browser and headless Node.js)
    saveToLocalStorage() {
        if (this.sitemap && typeof localStorage !== 'undefined') {
            try {
                localStorage.setItem('currentSitemap', JSON.stringify(this.sitemap));
                // Signal save event for UI indicators
                this.notifyListeners('storage:saved', { timestamp: Date.now() });
            } catch (e) {
                console.warn('Unable to persist sitemap to localStorage:', e);
            }
        }
    }
}

// Support both browser and Node.js module loading for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StateManager };
}

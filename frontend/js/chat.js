/**
 * Site Planner AI Chat Logic - Backend Integrated Version
 * Synchronizes with Django backend for dynamic questions and sitemap/wireframe generation.
 */

class AIChat {
    constructor() {
        // If the page is opened with ?reset=1, clear persisted localStorage keys
        try {
            if (typeof window !== 'undefined' && window.location && window.location.search && window.location.search.indexOf('reset=1') !== -1) {
                localStorage.removeItem('initialPrompt');
                localStorage.removeItem('currentSitemap');
                localStorage.removeItem('chatAiEnabled');
            }
        } catch (e) {
            // ignore storage errors in restricted environments
            console.warn('localStorage reset failed', e);
        }
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.skipBtn = document.getElementById('skipBtn');
        this.conversationArea = document.getElementById('conversationArea');
        this.quickActionsArea = document.querySelector('.quick-actions');
        this.primaryActionBtn = document.querySelector('.primary-action-btn');
        this.apiBaseUrl = '/api';
        this.aiToggle = document.getElementById('aiToggle');
        this.aiStatusBadge = document.getElementById('aiStatusBadge');
        this.aiConfig = null;
        this.aiEnabled = null;

        // Parsed brief preview/editor
        this.parsedPreview = document.getElementById('parsedPreview');
        this.parsedPreviewContent = document.getElementById('parsedPreviewContent');
        this.parsedConfidence = document.getElementById('parsedConfidence');
        this.editBriefBtn = document.getElementById('editBriefBtn');
        this.briefEditor = document.getElementById('briefEditor');
        this.applyBriefBtn = document.getElementById('applyBriefBtn');
        this.cancelBriefBtn = document.getElementById('cancelBriefBtn');
        this.editorFields = {
            client: document.getElementById('editClient'),
            type: document.getElementById('editType'),
            pages: document.getElementById('editPages'),
            services: document.getElementById('editServices'),
            features: document.getElementById('editFeatures'),
            goals: document.getElementById('editGoals'),
            showcase: document.getElementById('editShowcase'),
            style: document.getElementById('editStyle'),
            tone: document.getElementById('editTone'),
            language: document.getElementById('editLanguage'),
            trip_types: document.getElementById('editTripTypes'),
            passenger_types: document.getElementById('editPassengerTypes'),
            addons: document.getElementById('editAddons'),
            payments: document.getElementById('editPayments'),
            policies: document.getElementById('editPolicies')
        };

        // Summary elements
        this.summaryElements = {
            client: document.getElementById('summaryClient'),
            type: document.getElementById('summaryBusinessType'),
            showcase: document.getElementById('summaryShowcase'),
            services: document.getElementById('summaryServices'),
            goals: document.getElementById('summaryGoals'),
            features: document.getElementById('summaryFeatures'),
            tone: document.getElementById('summaryTone'),
            sitemap: document.getElementById('summarySitemap'),
            style: document.getElementById('summaryBrandStyle'),
            language: document.getElementById('summaryLanguage'),
            tripTypes: document.getElementById('summaryTripTypes'),
            passengerTypes: document.getElementById('summaryPassengerTypes'),
            addons: document.getElementById('summaryAddons'),
            payments: document.getElementById('summaryPayments'),
            policies: document.getElementById('summaryPolicies')
        };

        // State setup
        this.questions = []; // Populated from backend
        this.allQuestions = [];
        this.currentQuestionIndex = -1;
        this.currentMessages = [];
        this.sitemapData = null;
        this.userAnswers = {};
        this.parsedData = null;
        this.prefilledRendered = false;
        this.isChangingAnswer = false;
        this.nextInputType = null;
        this.changingQuestionId = null;
        this.lastSuggestedQuestionId = null;
        this.isSuggestionMode = false;
        this.briefCompleted = false;

        this.init();
    }

    init() {
        this.bindEvents();
        this.clearSummary();
        this.initializeUIWithPrompt();
        this.setupAutoResize();
        this.loadAIConfig().finally(() => this.startQuestionnaire());
    }

    getInitialPrompt() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlPrompt = urlParams.get('prompt');
        if (urlPrompt && urlPrompt.trim()) {
            localStorage.setItem('initialPrompt', urlPrompt.trim());
            return urlPrompt.trim();
        }
        const stored = localStorage.getItem('initialPrompt');
        return stored && stored.trim() ? stored.trim() : "General business website";
    }

    initializeUIWithPrompt() {
        const initialPrompt = this.getInitialPrompt();
        if (initialPrompt) {
            const words = initialPrompt.split(' ').filter(Boolean);
            const truncated = words.slice(0, 6).join(' ') + (words.length > 6 ? '...' : '');

            const projectName = document.getElementById('projectName');
            if (projectName) projectName.textContent = truncated || 'New Project';

            const summaryHeader = document.querySelector('.summary-header h1');
            if (summaryHeader) summaryHeader.textContent = 'Project Brief';
        }
    }

    clearSummary() {
        Object.values(this.summaryElements).forEach(el => {
            if (el) el.textContent = '...';
        });
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) progressFill.style.width = '0%';
    }

    bindEvents() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.handleSendMessage());
        }

        if (this.skipBtn) {
            this.skipBtn.addEventListener('click', () => this.handleSkipQuestion());
        }

        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }

        if (this.primaryActionBtn) {
            this.primaryActionBtn.addEventListener('click', () => this.handleFinalizeBrief());
        }

        if (this.editBriefBtn) {
            this.editBriefBtn.addEventListener('click', () => this.openBriefEditor());
        }

        if (this.applyBriefBtn) {
            this.applyBriefBtn.addEventListener('click', () => this.applyBriefEdits());
        }

        if (this.cancelBriefBtn) {
            this.cancelBriefBtn.addEventListener('click', () => this.closeBriefEditor());
        }

        if (this.aiToggle) {
            this.aiToggle.addEventListener('change', () => {
                const enabled = !!this.aiToggle.checked;
                this.aiEnabled = enabled;
                try {
                    localStorage.setItem('chatAiEnabled', enabled ? '1' : '0');
                } catch (e) {
                    // ignore storage errors
                }
                this.updateAiStatusBadge(enabled);
            });
        }
    }

    async loadAIConfig() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/config/`);
            const data = await response.json();
            this.aiConfig = data.ai && data.ai.chat ? data.ai.chat : {};
            const stored = (() => {
                try {
                    return localStorage.getItem('chatAiEnabled');
                } catch (e) {
                    return null;
                }
            })();
            let enabled = this.aiConfig && typeof this.aiConfig.enabled === 'boolean'
                ? this.aiConfig.enabled
                : false;
            if (stored === '1') enabled = true;
            if (stored === '0') enabled = false;
            this.aiEnabled = enabled;
            if (this.aiToggle) this.aiToggle.checked = !!enabled;
            this.updateAiStatusBadge(enabled);
        } catch (e) {
            this.aiEnabled = false;
            if (this.aiToggle) this.aiToggle.checked = false;
            this.updateAiStatusBadge(false);
        }
    }

    updateAiStatusBadge(enabled) {
        if (!this.aiStatusBadge) return;
        this.aiStatusBadge.textContent = enabled ? 'On' : 'Off';
        if (enabled) {
            this.aiStatusBadge.classList.add('on');
        } else {
            this.aiStatusBadge.classList.remove('on');
        }
    }

    setupAutoResize() {
        if (this.chatInput) {
            this.chatInput.addEventListener('input', () => this.triggerAutoResize());
        }
    }

    triggerAutoResize() {
        if (this.chatInput) {
            this.chatInput.style.height = 'auto';
            this.chatInput.style.height = (this.chatInput.scrollHeight) + 'px';
        }
    }

    normalizeAnswerValue(value) {
        if (Array.isArray(value)) {
            return value.map(v => String(v).trim()).filter(Boolean).join(', ');
        }
        if (value === null || value === undefined) return '';
        if (typeof value === 'object') return '';
        return String(value).trim();
    }

    applyParsedBrief(parsed) {
        if (!parsed || typeof parsed !== 'object') return;
        this.parsedData = parsed;
        this.updateTravelVisibility(parsed.type || '');
        const autoFilled = Array.isArray(parsed.auto_filled) ? new Set(parsed.auto_filled) : new Set();

        const fieldMap = {
            client: 'client',
            type: 'type',
            showcase: 'showcase',
            services: 'services',
            goals: 'goals',
            features: 'features',
            tone: 'tone',
            style: 'style',
            language: 'language',
            trip_types: 'tripTypes',
            passenger_types: 'passengerTypes',
            addons: 'addons',
            payments: 'payments',
            policies: 'policies'
        };

        Object.entries(fieldMap).forEach(([key, summaryField]) => {
            if (parsed[key]) {
                const value = this.normalizeAnswerValue(parsed[key]);
                if (value) {
                    if (!autoFilled.has(key)) {
                        this.userAnswers[key] = value;
                        this.updateSummaryField(summaryField, value);
                    }
                }
            }
        });

        let pagesText = '';
        if (parsed.pages_text) {
            pagesText = parsed.pages_text;
        } else if (Array.isArray(parsed.pages_tree)) {
            this.userAnswers.pages_tree = parsed.pages_tree;
            const names = this.flattenPagesTree(parsed.pages_tree);
            pagesText = names.join(', ');
        } else {
            pagesText = this.normalizeAnswerValue(parsed.pages);
        }
        if (pagesText) {
            this.userAnswers.pages = pagesText;
            this.updateSummaryField('sitemap', pagesText);
        }

        if (Object.keys(parsed).length > 0) {
            this.addMessage("I extracted details from your prompt. You can edit answers below or skip to finalize.", 'ai');
        }

        if (!this.userAnswers.client && parsed.type) {
            const projectName = document.getElementById('projectName');
            if (projectName) projectName.textContent = parsed.type;
            const summaryHeader = document.querySelector('.summary-header h1');
            if (summaryHeader) summaryHeader.textContent = `${parsed.type} - Brief Summary`;
        }

        this.updateParsedPreview(parsed);
    }

    updateTravelVisibility(typeValue) {
        const isTravel = /flight|airline|travel/i.test(typeValue || '');
        const travelItems = document.querySelectorAll('.summary-item.travel-only');
        travelItems.forEach(item => {
            item.style.display = isTravel ? 'block' : 'none';
        });
    }

    flattenPagesTree(tree) {
        const result = [];
        if (!Array.isArray(tree)) return result;
        const walk = (nodes) => {
            nodes.forEach(node => {
                if (!node || !node.name) return;
                result.push(String(node.name).trim());
                if (Array.isArray(node.children) && node.children.length) {
                    walk(node.children);
                }
            });
        };
        walk(tree);
        return result.filter(Boolean);
    }

    updateParsedPreview(parsed) {
        if (!this.parsedPreview || !this.parsedPreviewContent) return;

        const previewData = {
            client: this.userAnswers.client || parsed.client,
            type: this.userAnswers.type || parsed.type,
            pages: this.userAnswers.pages || parsed.pages_text,
            services: this.userAnswers.services || parsed.services,
            features: this.userAnswers.features || parsed.features,
            goals: this.userAnswers.goals || parsed.goals,
            showcase: this.userAnswers.showcase || parsed.showcase,
            style: this.userAnswers.style || parsed.style,
            tone: this.userAnswers.tone || parsed.tone,
            language: this.userAnswers.language || parsed.language,
            trip_types: this.userAnswers.trip_types || parsed.trip_types,
            passenger_types: this.userAnswers.passenger_types || parsed.passenger_types,
            addons: this.userAnswers.addons || parsed.addons,
            payments: this.userAnswers.payments || parsed.payments,
            policies: this.userAnswers.policies || parsed.policies
        };

        const lines = [];
        Object.entries(previewData).forEach(([key, value]) => {
            const normalized = this.normalizeAnswerValue(value);
            if (normalized) {
                const label = key.charAt(0).toUpperCase() + key.slice(1);
                lines.push(`${label}: ${normalized}`);
            }
        });
        this.parsedPreviewContent.textContent = lines.join('\n') || 'No structured data detected.';

        if (this.parsedConfidence && typeof parsed.confidence === 'number') {
            const pct = Math.round(parsed.confidence * 100);
            this.parsedConfidence.textContent = `Confidence: ${pct}%`;
        }

        this.parsedPreview.style.display = 'block';
    }

    openBriefEditor() {
        if (!this.briefEditor) return;
        Object.entries(this.editorFields).forEach(([key, input]) => {
            if (!input) return;
            input.value = this.normalizeAnswerValue(this.userAnswers[key] || (this.parsedData && this.parsedData[key]) || '');
        });
        if (this.parsedPreview) this.parsedPreview.style.display = 'none';
        this.briefEditor.style.display = 'block';
    }

    applyBriefEdits() {
        if (!this.briefEditor) return;
        const summaryMap = {
            type: 'type',
            trip_types: 'tripTypes',
            passenger_types: 'passengerTypes',
            addons: 'addons',
            payments: 'payments',
            policies: 'policies'
        };
        Object.entries(this.editorFields).forEach(([key, input]) => {
            if (!input) return;
            const value = this.normalizeAnswerValue(input.value);
            if (value) {
                this.userAnswers[key] = value;
                if (key === 'pages') {
                    delete this.userAnswers.pages_tree;
                    this.updateSummaryField('sitemap', value);
                } else {
                    const summaryField = summaryMap[key] || key;
                    this.updateSummaryField(summaryField, value);
                }
            }
        });
        this.updateParsedPreview(this.parsedData || {});
        this.closeBriefEditor();
    }

    closeBriefEditor() {
        if (this.briefEditor) this.briefEditor.style.display = 'none';
        if (this.parsedPreview) this.parsedPreview.style.display = 'block';
    }

    async startQuestionnaire() {
        const initialPrompt = this.getInitialPrompt();

        const indicator = this.showTypingIndicator();
        try {
            const response = await fetch(`${this.apiBaseUrl}/init-brief/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: initialPrompt, ai_enabled: this.aiEnabled })
            });
            const data = await response.json();
            if (indicator) indicator.remove();

            if (data.success && data.questions) {
                let questions = data.questions;
                this.allQuestions = Array.isArray(data.questions) ? data.questions.slice() : [];
                if (data.parsed) {
                    this.applyParsedBrief(data.parsed);
                    if (Array.isArray(data.parsed.missing_fields) && data.parsed.missing_fields.length) {
                        const missingSet = new Set(data.parsed.missing_fields);
                        questions = questions.filter(q => missingSet.has(q.id));
                    }
                }
                if (data.ai_error) {
                    // Suppress user-facing AI error bubbles; keep console visibility for debugging.
                    console.warn('AI suggestions error:', data.ai_error);
                }
                this.renderPrefilledConversation(data.questions);
                this.questions = questions;
                if (!this.questions.length) {
                    this.finishBrief();
                    return;
                }
                this.nextQuestion();
            } else {
                this.addMessage("I'm having trouble initializing the brief. Please try again.", 'ai');
            }
        } catch (error) {
            if (indicator) indicator.remove();
            console.error('Error:', error);
            this.addMessage("Connection error. Please ensure the backend is running.", 'ai');
        }
    }

    renderPrefilledConversation(questions) {
        if (this.prefilledRendered) return;
        if (!Array.isArray(questions)) return;
        questions.forEach(q => {
            const answer = this.userAnswers[q.id];
            if (answer) {
                this.addMessage(q.text, 'ai');
                this.addMessage(answer, 'user');
            }
        });
        this.prefilledRendered = true;
    }

    nextQuestion() {
        if (this.isChangingAnswer) {
            this.isChangingAnswer = false;
            this.changingQuestionId = null;
        }

        this.currentQuestionIndex++;

        if (this.currentQuestionIndex < this.questions.length) {
            const question = this.questions[this.currentQuestionIndex];
            const existingAnswer = this.userAnswers[question.id];
            if (existingAnswer) {
                this.updateSummaryField(question.summaryField, this.normalizeAnswerValue(existingAnswer));
                return this.nextQuestion();
            }
            this.addMessage(question.text, 'ai');
            this.renderOptions(question.options, question.multiSelect, question.id);
        } else {
            this.finishBrief();
        }
    }

    renderOptions(options, isMultiSelect = false, questionId = null) {
        if (!this.quickActionsArea) return;
        this.quickActionsArea.innerHTML = '';

        const finalOptions = this.ensureMinOptions(options || [], questionId);

        finalOptions.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'quick-btn';
            btn.textContent = opt;

            btn.addEventListener('click', () => {
                if (isMultiSelect) {
                    const currentValue = this.chatInput.value.trim();
                    if (currentValue) {
                        this.chatInput.value = currentValue + ', ' + opt;
                    } else {
                        this.chatInput.value = opt;
                    }
                    this.chatInput.focus();
                    this.triggerAutoResize();
                    btn.classList.add('active-opt');
                    setTimeout(() => btn.classList.remove('active-opt'), 300);
                } else {
                    this.handleUserAnswer(opt);
                }
            });
            this.quickActionsArea.appendChild(btn);
        });
    }

    ensureMinOptions(options, questionId) {
        const qid = (questionId || '').toLowerCase();
        if (qid === 'language') return ['English'];
        const opts = (options || []).map(o => String(o).trim()).filter(Boolean);
        if (opts.length >= 4) return opts;
        const topUps = this.buildFallbackOptions(qid);
        topUps.forEach(opt => opts.push(opt));
        // Deduplicate
        const seen = new Set();
        const deduped = [];
        for (const opt of opts) {
            const key = opt.toLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            deduped.push(opt);
        }
        return deduped.slice(0, 5);
    }

    buildFallbackOptions(questionId) {
        const qid = (questionId || '').toLowerCase();
        const prompt = (localStorage.getItem('initialPrompt') || '').toLowerCase();
        const parsed = this.parsedData || {};
        const base = this.extractPromptBase(prompt, parsed);

        if (qid === 'showcase') {
            if (/(store|shop|shopping|product|cart|checkout)/i.test(prompt)) {
                return ['Product Browsing', 'Featured Collections', 'Discovery & Filtering', 'Cart & Checkout'];
            }
            if (/(restaurant|cafe|food|menu|chef)/i.test(prompt)) {
                return ['Menu Showcase', 'Table Reservations', 'Dining Experience', 'Chef Specials'];
            }
            return [`${base} Showcase`, `${base} Experience`, `${base} Discovery`, `${base} Focus`];
        }
        if (qid === 'style') {
            return [`${base} Modern`, `${base} Clean`, `${base} Minimal`, `${base} Bright`];
        }
        if (qid === 'tone') {
            return [`${base} Friendly`, `${base} Professional`, `${base} Trustworthy`, `${base} Calm`];
        }
        if (qid === 'goals') {
            return [`Improve ${base} experience`, `Increase ${base} engagement`, `Build trust in ${base}`, `Boost conversions`];
        }
        if (qid === 'services' || qid === 'features') {
            return [`${base} Services`, `${base} Features`, `${base} Tools`, `${base} Support`];
        }
        if (qid === 'pages') {
            return [`${base} Overview`, `${base} Details`, 'Contact', 'Home'];
        }
        return [`${base} Option 1`, `${base} Option 2`, `${base} Option 3`, `${base} Option 4`];
    }

    extractPromptBase(prompt, parsed) {
        const type = (parsed && parsed.type) ? String(parsed.type).split(' ')[0] : '';
        if (type) return type;
        const match = (prompt || '').match(/[a-z][a-z0-9]{2,}/i);
        return match ? match[0][0].toUpperCase() + match[0].slice(1) : 'Site';
    }

    handleUserAnswer(answer) {
        this.addMessage(answer, 'user');

        let question;
        if (this.isChangingAnswer && this.changingQuestionId) {
            question = this.questions.find(q => q.id === this.changingQuestionId);
        } else {
            question = this.questions[this.currentQuestionIndex];
        }
        if (!question && this.lastSuggestedQuestionId) {
            question = this.allQuestions.find(q => q.id === this.lastSuggestedQuestionId)
                || this.questions.find(q => q.id === this.lastSuggestedQuestionId);
        }

        if (question) {
            this.userAnswers[question.id] = answer;
            this.updateSummaryField(question.summaryField, answer);
        }

        // Update progress
        const answeredCount = Object.keys(this.userAnswers).length;
        const progress = (answeredCount / this.questions.length) * 100;
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) progressFill.style.width = `${progress}%`;

        // Clear input
        if (this.chatInput) {
            this.chatInput.value = '';
            this.chatInput.style.height = 'auto';
        }

        // Slight delay for AI feel
        const currentQ = this.questions[this.currentQuestionIndex];
        const answeredCurrent = currentQ && question && currentQ.id === question.id;
        const isComplete = answeredCount >= this.questions.length;

        setTimeout(() => {
            if (this.isSuggestionMode) {
                this.isSuggestionMode = false;
                this.lastSuggestedQuestionId = null;
                if (this.quickActionsArea) this.quickActionsArea.innerHTML = '';
                if (isComplete) {
                    this.finishBrief();
                } else if (answeredCurrent) {
                    this.nextQuestion();
                }
                return;
            }
            if (this.isChangingAnswer) {
                this.addMessage("Got it. I've updated that for you. Let's continue.", 'ai');
                this.isChangingAnswer = false;
                this.changingQuestionId = null;
                const currentQ = this.questions[this.currentQuestionIndex];
                if (currentQ) {
                    this.addMessage(currentQ.text, 'ai');
                    this.renderOptions(currentQ.options, currentQ.multiSelect);
                }
            } else {
                this.nextQuestion();
            }
        }, 600);
    }

    handleSkipQuestion() {
        if (this.currentQuestionIndex >= 0 && this.currentQuestionIndex < this.questions.length) {
            const question = this.questions[this.currentQuestionIndex];
            this.addMessage(`Skipping ${question.id}...`, 'user');

            this.userAnswers[question.id] = "Skipped";
            this.updateSummaryField(question.summaryField, "Not specified");

            setTimeout(() => {
                this.nextQuestion();
            }, 400);
        }
    }

    handleSendMessage() {
        if (!this.chatInput) return;
        const message = this.chatInput.value.trim();
        if (!message) return;

        // If user pastes a long prompt before answering, treat it as a new prompt
        if (!this.userAnswers.client && this.currentQuestionIndex <= 0) {
            const looksLikePrompt = message.length > 80 && /page|pages|website|dashboard|flight|booking/i.test(message);
            if (looksLikePrompt) {
                localStorage.setItem('initialPrompt', message);
                this.chatInput.value = '';
                this.conversationArea.innerHTML = '';
                this.currentQuestionIndex = -1;
                this.questions = [];
                this.userAnswers = {};
                this.parsedData = null;
                this.clearSummary();
                this.initializeUIWithPrompt();
                this.startQuestionnaire();
                return;
            }
        }

        // Check for "change answer" request
        const lowerMsg = message.toLowerCase();
        const isSuggestionRequest = /(suggest|recommend|ideas?|options?)/i.test(lowerMsg);
        if (isSuggestionRequest) {
            const suggestionTargets = [
                { id: 'pages', keywords: ['page', 'pages', 'sitemap'] },
                { id: 'features', keywords: ['feature', 'features'] },
                { id: 'services', keywords: ['service', 'services', 'offerings'] },
                { id: 'goals', keywords: ['goal', 'goals'] },
                { id: 'style', keywords: ['style', 'design', 'palette', 'color'] },
                { id: 'tone', keywords: ['tone', 'voice', 'personality'] },
                { id: 'showcase', keywords: ['primary function', 'purpose', 'function'] },
                { id: 'language', keywords: ['language', 'locale'] },
                { id: 'trip_types', keywords: ['trip', 'journey'] },
                { id: 'passenger_types', keywords: ['passenger'] },
                { id: 'addons', keywords: ['add-on', 'addon', 'add ons'] },
                { id: 'payments', keywords: ['payment', 'pay'] },
                { id: 'policies', keywords: ['policy', 'policies', 'refund', 'cancellation'] }
            ];
            const target = suggestionTargets.find(t => t.keywords.some(k => lowerMsg.includes(k)));
            if (target) {
                const q = this.allQuestions.find(q => q.id === target.id) || this.questions.find(q => q.id === target.id);
                if (q) {
                    this.addMessage(message, 'user');
                    this.chatInput.value = '';
                    this.isSuggestionMode = true;
                    this.lastSuggestedQuestionId = q.id;
                    this.addMessage(`Here are suggested options for ${q.text}`, 'ai');
                    this.renderOptions(q.options, q.multiSelect, q.id);
                    return;
                }
                // Fallback to parsed data if we have it
                if (target.id === 'pages' && this.parsedData) {
                    const pagesText = this.parsedData.pages_text || (Array.isArray(this.parsedData.pages_tree) ? this.flattenPagesTree(this.parsedData.pages_tree).join(', ') : '');
                    if (pagesText) {
                        this.addMessage(message, 'user');
                        this.chatInput.value = '';
                        this.isSuggestionMode = true;
                        this.lastSuggestedQuestionId = 'pages';
                        this.addMessage(`Here are suggested options for pages:`, 'ai');
                        this.renderOptions(pagesText.split(',').map(s => s.trim()).filter(Boolean), false, 'pages');
                        return;
                    }
                }
            }
            this.addMessage(message, 'user');
            this.chatInput.value = '';
            this.addMessage("I don't have suggestions for that yet. Try asking during the questionnaire or provide more details.", 'ai');
            return;
        }
        if (lowerMsg.includes('change') && lowerMsg.includes('answer')) {
            this.addMessage(message, 'user');
            this.chatInput.value = '';

            let targetQuestion = null;

            // Try to find matching question by text or ID
            for (const q of this.questions) {
                const questionText = q.text.toLowerCase();
                const questionId = q.id.toLowerCase();

                // Match if user input contains the question ID or a significant part of the question text
                if (lowerMsg.includes(questionId) || lowerMsg.includes(questionText) || questionText.includes(lowerMsg.replace(/i want to change answer/g, '').trim())) {
                    targetQuestion = q;
                    break;
                }
            }

            if (!targetQuestion) {
                targetQuestion = this.questions[this.currentQuestionIndex - 1] || this.questions[0];
            }

            if (targetQuestion) {
                this.isChangingAnswer = true;
                this.changingQuestionId = targetQuestion.id;
                const prevAnswer = this.userAnswers[targetQuestion.id] || "nothing yet";
                this.addMessage(`You previously mentioned ${prevAnswer} for this.`, 'ai');
                this.addMessage(`What would you like to change it to?`, 'ai');
                this.renderOptions(targetQuestion.options, targetQuestion.multiSelect, targetQuestion.id);
            } else {
                this.addMessage("I'm not sure which answer you'd like to change. Could you specify?", 'ai');
            }
            return;
        }

        this.handleUserAnswer(message);
    }

    addMessage(text, sender) {
        if (!this.conversationArea) return;

        const messageBubble = document.createElement('div');
        messageBubble.className = `${sender}-message message-bubble`;

        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = text.replace(/\n/g, '<br>');

        messageBubble.appendChild(content);
        this.conversationArea.appendChild(messageBubble);
        this.scrollToBottom();

        return messageBubble;
    }

    updateSummaryField(field, value) {
        const el = this.summaryElements[field];
        if (el) {
            const displayValue = value;
            el.textContent = displayValue;
            el.style.color = '#111827';
            el.style.fontWeight = '600';

            // Also update project name in header if this is the client field
            if (field === 'client' && value && value !== '...' && value !== 'Skipped') {
                const projectName = document.getElementById('projectName');
                if (projectName) {
                    projectName.textContent = value;
                }
                const summaryHeader = document.querySelector('.summary-header h1');
                if (summaryHeader) {
                    summaryHeader.textContent = `${value} - Brief Summary`;
                }
            }

            el.animate([
                { opacity: 0.5, transform: 'translateY(2px)' },
                { opacity: 1, transform: 'translateY(0)' }
            ], { duration: 300, easing: 'ease-out' });
        }
    }

    finishBrief() {
        if (this.conversationArea) {
            const existing = this.conversationArea.querySelectorAll('.final-brief-message');
            existing.forEach(node => node.remove());
        }
        this.briefCompleted = true;
        const bubble = this.addMessage("Excellent! I have all the information I need. You can review the summary or click 'Use this brief' to generate your professional sitemap and wireframes.", 'ai');
        if (bubble) bubble.classList.add('final-brief-message');
        if (this.quickActionsArea) this.quickActionsArea.innerHTML = '';
    }

    async handleFinalizeBrief() {
        if (Object.keys(this.userAnswers).length < 2) {
            alert('Please answer at least a few questions before finalizing.');
            return;
        }

        const originalBtnText = this.primaryActionBtn.innerHTML;
        this.primaryActionBtn.innerHTML = '<span class="loader"></span> Generating...';
        this.primaryActionBtn.disabled = true;
        const initialPrompt = localStorage.getItem('initialPrompt') || '';

        try {
            // 1. Generate Sitemap
            const sitemapRes = await fetch(`${this.apiBaseUrl}/generate-sitemap/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: initialPrompt || "Brief integrated generation",
                    brief_data: this.userAnswers
                })
            });
            const sitemapData = await sitemapRes.json();

            if (sitemapData.success) {
                // 2. Generate Wireframes
                const wireframeRes = await fetch(`${this.apiBaseUrl}/generate-wireframe/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sitemap_data: sitemapData.sitemap })
                });
                const wireframeData = await wireframeRes.json();

                if (wireframeData.success) {
                    const wireframesMap = wireframeData.wireframes.wireframes;

                    // Attach wireframe sections to each page in the sitemap
                    const attachSections = (pages) => {
                        pages.forEach(page => {
                            if (wireframesMap[page.id]) {
                                page.sections = wireframesMap[page.id].sections;
                            }
                            if (page.children) attachSections(page.children);
                        });
                    };
                    attachSections(sitemapData.sitemap.pages);

                    localStorage.setItem('currentSitemap', JSON.stringify(sitemapData.sitemap));
                    window.location.href = 'index.html#editor';
                } else {
                    alert('Wireframe generation failed.');
                }
            } else {
                alert('Sitemap generation failed.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('A connection error occurred during generation.');
        } finally {
            this.primaryActionBtn.innerHTML = originalBtnText;
            this.primaryActionBtn.disabled = false;
        }
    }

    showTypingIndicator() {
        if (!this.conversationArea) return;
        const container = document.createElement('div');
        container.className = 'ai-message message-bubble typing-container';
        container.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.conversationArea.appendChild(container);
        this.scrollToBottom();
        return container;
    }

    scrollToBottom() {
        if (this.conversationArea) {
            this.conversationArea.scrollTo({
                top: this.conversationArea.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AIChat();
});

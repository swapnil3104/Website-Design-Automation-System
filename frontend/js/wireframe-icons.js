window.WireframeIconLibrary = (() => {
    const emoji = {
        navigation: ['🏠', '📄', '🧭', '📚', '📞', '🔍', '👤', '⚙️'],
        hero: ['🚀', '✨', '🌟', '🎯', '💡', '🔥', '📈', '🏆'],
        features: ['⚡', '🔒', '🛡️', '📊', '🎨', '🧠', '🔗', '📱'],
        services: ['🧩', '🛠️', '📦', '🚚', '💼', '📣', '🧪', '🧱'],
        business: ['🏢', '📈', '💼', '🤝', '💳', '🧾', '🏦', '📉'],
        ecommerce: ['🛒', '🏷️', '📦', '💳', '🚚', '🎁', '🧺', '⭐'],
        marketing: ['📣', '🎯', '📢', '🧲', '📬', '📱', '📊', '🔥'],
        content: ['📝', '📚', '📰', '🎬', '🖼️', '🎤', '✍️', '📖'],
        social: ['👍', '💬', '❤️', '🔔', '📢', '👥', '🌐', '📱'],
        team: ['👤', '👥', '🧑‍💼', '🧑‍💻', '🤝', '🎓', '🏅', '🌍'],
        contact: ['📞', '✉️', '📍', '🕒', '💬', '📠', '🌐', '🧭'],
        testimonial: ['⭐', '💬', '❤️', '👏', '🏅', '🌟', '✅', '🙌'],
        pricing: ['💲', '💳', '🧾', '📦', '🏷️', '💼', '🏆', '✅'],
        stats: ['📊', '📈', '📉', '🏆', '⏱️', '🌍', '👥', '🎯'],
        faq: ['❓', '💡', '📘', '🛟', '🔎', '🧠', '📌', '✅'],
        footer: ['🔗', '📍', '✉️', '📞', '🌐', '🔒', '📄', '©️'],
        blog: ['📰', '✍️', '📚', '🗂️', '🕘', '🏷️', '🎤', '📖'],
        gallery: ['🖼️', '📷', '🎬', '🎨', '📸', '🧿', '🧵', '🌄'],
        travel: ['✈️', '🧳', '🛫', '🛬', '🏨', '🪪', '🗺️', '🌍'],
        education: ['🎓', '📘', '🧠', '📝', '🏫', '📖', '🧪', '💻'],
        healthcare: ['🩺', '💊', '🏥', '❤️', '🧬', '🩹', '🧑‍⚕️', '📋']
    };

    const svg = {
        home: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 10.5L12 3l9 7.5"></path>
                <path d="M5 9.5V21h14V9.5"></path>
            </svg>
        `,
        search: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="M21 21l-4.35-4.35"></path>
            </svg>
        `,
        user: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="4"></circle>
                <path d="M4 20c1.5-4 5-6 8-6s6.5 2 8 6"></path>
            </svg>
        `,
        settings: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.04 1.56V22a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 8.96 20.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.04H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.65 8.4a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1.04-1.56V3a2 2 0 1 1 4 0v.09A1.7 1.7 0 0 0 15 4.65a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.64.24 1.13.77 1.33 1.44.2.68.09 1.41-.3 1.99-.39.58-1.01.95-1.72 1.03-.71.08-1.42-.13-1.97-.58z"></path>
            </svg>
        `,
        sparkles: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8L12 3z"></path>
                <path d="M19 14l.9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14z"></path>
                <path d="M5 14l.9 2.1L8 17l-2.1.9L5 20l-.9-2.1L2 17l2.1-.9L5 14z"></path>
            </svg>
        `,
        lightning: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"></path>
            </svg>
        `,
        shield: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 3l7 3v6c0 5-3.5 8-7 9-3.5-1-7-4-7-9V6l7-3z"></path>
            </svg>
        `,
        chart: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19h16"></path>
                <path d="M7 16V9"></path>
                <path d="M12 16V5"></path>
                <path d="M17 16v-4"></path>
            </svg>
        `,
        card: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="5" width="18" height="14" rx="2"></rect>
                <path d="M3 10h18"></path>
            </svg>
        `,
        briefcase: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="7" width="18" height="13" rx="2"></rect>
                <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
        `,
        mail: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="5" width="18" height="14" rx="2"></rect>
                <path d="M3 7l9 6 9-6"></path>
            </svg>
        `,
        phone: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.4 19.4 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4 2h3a2 2 0 0 1 2 1.7l.5 3a2 2 0 0 1-.6 1.8l-1.3 1.3a16 16 0 0 0 6.6 6.6l1.3-1.3a2 2 0 0 1 1.8-.6l3 .5a2 2 0 0 1 1.7 2z"></path>
            </svg>
        `,
        mapPin: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 21s-6-4.35-6-10a6 6 0 1 1 12 0c0 5.65-6 10-6 10z"></path>
                <circle cx="12" cy="11" r="2.5"></circle>
            </svg>
        `,
        star: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.8 6.4 20.2l1.1-6.2L3 9.6l6.2-.9L12 3z"></path>
            </svg>
        `,
        image: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="5" width="18" height="14" rx="2"></rect>
                <circle cx="9" cy="10" r="1.5"></circle>
                <path d="M21 16l-5-5-7 7"></path>
            </svg>
        `,
        globe: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M3 12h18"></path>
                <path d="M12 3a15 15 0 0 1 0 18"></path>
                <path d="M12 3a15 15 0 0 0 0 18"></path>
            </svg>
        `,
        faq: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M9.5 9a2.5 2.5 0 1 1 4.3 1.7c-.8.8-1.8 1.4-1.8 2.8"></path>
                <circle cx="12" cy="17" r="1"></circle>
            </svg>
        `
    };

    const sectionDefaults = {
        navbar: { emoji: '🧭', icon: 'home' },
        hero: { emoji: '🚀', icon: 'sparkles' },
        features: { emoji: '⚡', icon: 'lightning' },
        services: { emoji: '🛠️', icon: 'briefcase' },
        service: { emoji: '🛠️', icon: 'briefcase' },
        content: { emoji: '📝', icon: 'card' },
        information: { emoji: '📘', icon: 'card' },
        info: { emoji: '📘', icon: 'card' },
        pricing: { emoji: '💳', icon: 'card' },
        testimonial: { emoji: '⭐', icon: 'star' },
        blog: { emoji: '📰', icon: 'image' },
        gallery: { emoji: '🖼️', icon: 'image' },
        contact: { emoji: '📞', icon: 'phone' },
        'contact-form': { emoji: '✉️', icon: 'mail' },
        'contact-details': { emoji: '📍', icon: 'mapPin' },
        location: { emoji: '🗺️', icon: 'mapPin' },
        team: { emoji: '👥', icon: 'user' },
        faq: { emoji: '❓', icon: 'faq' },
        footer: { emoji: '🌐', icon: 'globe' },
        stats: { emoji: '📊', icon: 'chart' },
        cta: { emoji: '🎯', icon: 'sparkles' }
    };

    function normalizeKey(value) {
        return String(value || '').trim().toLowerCase();
    }

    function getEmojiGroup(group) {
        return emoji[normalizeKey(group)] || [];
    }

    function getEmoji(group, index = 0) {
        const pool = getEmojiGroup(group);
        if (!pool.length) return '✨';
        return pool[Math.abs(index) % pool.length];
    }

    function getIconSvg(name) {
        return svg[normalizeKey(name)] || svg.sparkles;
    }

    function getSectionVisual(sectionType, index = 0) {
        const key = normalizeKey(sectionType);
        const config = sectionDefaults[key] || { emoji: '✨', icon: 'sparkles' };
        return {
            emoji: config.emoji || getEmoji(key, index),
            iconName: config.icon,
            iconSvg: getIconSvg(config.icon)
        };
    }

    return {
        emoji,
        svg,
        sectionDefaults,
        getEmojiGroup,
        getEmoji,
        getIconSvg,
        getSectionVisual
    };
})();
